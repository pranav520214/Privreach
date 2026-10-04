"""In-RAM Okapi BM25 implementation optimized for scientific and chemical literature."""

import math
import re
from collections import Counter
from typing import List, Tuple, Dict
from privearch.schemas import DocumentChunk


def tokenize_scientific(text: str) -> List[str]:
    """Tokenize scientific text while retaining chemical formulas, numbers, and units."""
    text = text.lower()
    # Match alphanumeric sequences and chemical terms (e.g. h2o, nacl, ph, 298k)
    tokens = re.findall(r'[a-zA-Z0-9_\-\.\+]+', text)
    # Filter pure single punctuation
    clean_tokens = [t.strip('.-_+') for t in tokens if len(t.strip('.-_+')) > 1]
    return clean_tokens


class InRamBM25:
    """
    High-speed In-RAM Okapi BM25 index.
    Dynamically updatable upon dragging and dropping new PDFs.
    """
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.chunks: List[DocumentChunk] = []
        self.doc_len: List[int] = []
        self.avg_doc_len: float = 0.0
        self.total_docs: int = 0
        self.term_freqs: List[Counter] = []
        self.doc_freqs: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}

    def add_chunks(self, new_chunks: List[DocumentChunk]) -> None:
        """Dynamically add new document chunks and update the index in RAM."""
        if not new_chunks:
            return

        for chunk in new_chunks:
            tokens = tokenize_scientific(chunk.text)
            tf = Counter(tokens)
            self.chunks.append(chunk)
            self.term_freqs.append(tf)
            self.doc_len.append(len(tokens))

            # Update document frequencies
            for term in tf.keys():
                self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1

        self.total_docs = len(self.chunks)
        self.avg_doc_len = sum(self.doc_len) / self.total_docs if self.total_docs > 0 else 0.0

        # Recalculate IDFs
        self._calculate_idf()

    def _calculate_idf(self) -> None:
        """Calculate Robertson-Spärck Jones IDF for all terms in vocabulary."""
        self.idf.clear()
        for term, df in self.doc_freqs.items():
            # Standard BM25 IDF formulation with smoothing
            val = math.log((self.total_docs - df + 0.5) / (df + 0.5) + 1.0)
            self.idf[term] = max(val, 0.01)

    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """
        Rank all indexed chunks for the given query.
        
        Returns:
            List of (chunk_index, bm25_score) tuples, sorted descending.
        """
        if self.total_docs == 0:
            return []

        q_tokens = tokenize_scientific(query)
        if not q_tokens:
            return []

        scores = [0.0] * self.total_docs

        for term in q_tokens:
            if term not in self.idf:
                continue
            term_idf = self.idf[term]

            for i in range(self.total_docs):
                f = self.term_freqs[i].get(term, 0)
                if f == 0:
                    continue
                d_len = self.doc_len[i]
                numerator = f * (self.k1 + 1.0)
                denominator = f + self.k1 * (1.0 - self.b + self.b * (d_len / self.avg_doc_len))
                scores[i] += term_idf * (numerator / denominator)

        # Pair with indices and sort
        indexed_scores = [(idx, score) for idx, score in enumerate(scores) if score > 0.0]
        indexed_scores.sort(key=lambda x: x[1], reverse=True)
        return indexed_scores[:top_k]

    def clear(self) -> None:
        """Reset index."""
        self.chunks.clear()
        self.doc_len.clear()
        self.avg_doc_len = 0.0
        self.total_docs = 0
        self.term_freqs.clear()
        self.doc_freqs.clear()
        self.idf.clear()
