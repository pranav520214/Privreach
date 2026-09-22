import json
import re
from rank_bm25 import BM25Okapi

class BM25Retriever:
    def __init__(self):
        self.corpus = []
        self.bm25 = None
        self.tokenized_corpus = []

    def load_corpus(self, jsonl_path: str):
        """
        Loads the retrieval corpus from the given JSONL file.
        """
        self.corpus = []
        self.tokenized_corpus = []
        
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                record = json.loads(line)
                self.corpus.append(record)
                
                # Simple tokenization for BM25: lowercase and split by non-alphanumeric
                text = record.get("text", "")
                tokens = self._tokenize(text)
                self.tokenized_corpus.append(tokens)
                
        if self.tokenized_corpus:
            self.bm25 = BM25Okapi(self.tokenized_corpus)

    def add_chunks(self, chunks: list[dict]):
        if not chunks: return
        for record in chunks:
            self.corpus.append(record)
            tokens = self._tokenize(record.get("text", ""))
            self.tokenized_corpus.append(tokens)
            
        # Rebuild BM25 index (BM25Okapi doesn't support live append well, fast enough to rebuild)
        self.bm25 = BM25Okapi(self.tokenized_corpus)
        print(f"Dynamically rebuilt BM25 Index with {len(chunks)} new chunks.")

    def _tokenize(self, text: str):
        text = text.lower()
        return [t for t in re.split(r'[^a-z0-9]+', text) if t]

    def search(self, query: str, top_k: int = 10):
        if not self.bm25:
            return []
            
        tokenized_query = self._tokenize(query)
        # Get raw scores
        scores = self.bm25.get_scores(tokenized_query)
        
        # Get top-k indices
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        
        results = []
        for i in top_indices:
            if scores[i] > 0:  # Only return if there's some match
                result = self.corpus[i].copy()
                result["score"] = float(scores[i])
                results.append(result)
                
        return results
