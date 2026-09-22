import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

class VectorRetriever:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        # We use a lightweight model suitable for CPU-only inference if needed.
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.corpus = []
        
    def build_index(self, jsonl_path: str):
        """
        Builds the FAISS index from the given retrieval JSONL corpus.
        """
        self.corpus = []
        texts = []
        
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                record = json.loads(line)
                self.corpus.append(record)
                texts.append(record.get("text", ""))
                
        if not texts:
            return
            
        print(f"Encoding {len(texts)} chunks for vector search...")
        # Encode all texts
        embeddings = self.model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
        
        # Initialize FAISS Index (L2 distance)
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings)
        print("Index built successfully.")
        
    def add_chunks(self, chunks: list[dict]):
        if not chunks: return
        texts = [c.get("text", "") for c in chunks]
        embeddings = self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        
        if self.index is None:
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
            
        self.index.add(embeddings)
        self.corpus.extend(chunks)
        print(f"Dynamically added {len(chunks)} chunks to Vector Index.")
        
    def search(self, query: str, top_k: int = 10):
        if self.index is None:
            return []
            
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        
        # FAISS search returns squared L2 distances (lower is better)
        distances, indices = self.index.search(query_embedding, top_k)
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx != -1:
                result = self.corpus[idx].copy()
                # Convert distance to a similarity-like score (inverting L2)
                # A simple inversion: 1 / (1 + distance)
                result["score"] = 1.0 / (1.0 + float(dist))
                results.append(result)
                
        return results
