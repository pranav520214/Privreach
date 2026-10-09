"""In-RAM FAISS-compatible dense vector index with pure-NumPy acceleration fallback."""

from typing import List, Tuple, Optional
import numpy as np
from privearch.schemas import DocumentChunk


class InRamVectorIndex:
    """
    In-RAM Dense Vector Index for semantic similarity search.
    Supports dynamic vector additions upon dropping new PDFs.
    """
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.chunks: List[DocumentChunk] = []
        self.vectors: Optional[np.ndarray] = None
        self._use_faiss = False
        self._faiss_index = None

        try:
            import faiss
            self._faiss = faiss
            self._faiss_index = faiss.IndexFlatIP(dimension)
            self._use_faiss = True
        except ImportError:
            self._use_faiss = False

    def add_vectors(self, new_vectors: np.ndarray, new_chunks: List[DocumentChunk]) -> None:
        """Dynamically add embedding vectors and chunk metadata to the index in RAM."""
        if len(new_vectors) == 0:
            return

        if new_vectors.shape[1] != self.dimension:
            # Reinitialize index dimension if different (e.g. switching between 384 and 1024 models)
            self.dimension = new_vectors.shape[1]
            if self._use_faiss:
                self._faiss_index = self._faiss.IndexFlatIP(self.dimension)
            self.vectors = None
            self.chunks.clear()

        # Ensure float32
        new_vectors = new_vectors.astype(np.float32)

        # Ensure L2 normalization
        norms = np.linalg.norm(new_vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1e-9
        normalized_vectors = new_vectors / norms

        if self.vectors is None:
            self.vectors = normalized_vectors
        else:
            self.vectors = np.vstack([self.vectors, normalized_vectors])

        self.chunks.extend(new_chunks)

        if self._use_faiss and self._faiss_index is not None:
            self._faiss_index.add(normalized_vectors)

    def search(self, query_vector: np.ndarray, top_k: int = 10) -> List[Tuple[int, float]]:
        """
        Search top_k most similar chunks by cosine similarity.
        
        Returns:
            List of (chunk_index, similarity_score) tuples, sorted descending.
        """
        if self.vectors is None or len(self.chunks) == 0:
            return []

        # Ensure shape and normalization
        q_vec = query_vector.astype(np.float32).reshape(1, -1)
        norm = np.linalg.norm(q_vec)
        if norm > 0:
            q_vec = q_vec / norm

        top_k = min(top_k, len(self.chunks))

        if self._use_faiss and self._faiss_index is not None:
            distances, indices = self._faiss_index.search(q_vec, top_k)
            results = []
            for idx, dist in zip(indices[0], distances[0]):
                if idx >= 0:
                    results.append((int(idx), float(dist)))
            return results

        # Vectorized NumPy fallback
        scores = np.dot(self.vectors, q_vec.T).flatten()
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [(int(idx), float(scores[idx])) for idx in top_indices]

    def clear(self) -> None:
        """Reset index."""
        self.chunks.clear()
        self.vectors = None
        if self._use_faiss and self._faiss is not None:
            self._faiss_index = self._faiss.IndexFlatIP(self.dimension)
