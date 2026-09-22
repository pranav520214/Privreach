from typing import List, Dict
from core.schemas.retrieval_schemas import RetrievedChunk, EvidencePackage
from knowledge.retrieval.bm25_retriever import BM25Retriever
from knowledge.retrieval.vector_retriever import VectorRetriever

class HybridRetriever:
    def __init__(self, corpus_path: str):
        self.corpus_path = corpus_path
        self.bm25 = BM25Retriever()
        self.vector = VectorRetriever()
        
    def initialize(self):
        print("Initializing BM25 Index...")
        self.bm25.load_corpus(self.corpus_path)
        print("Initializing Dense Vector Index...")
        self.vector.build_index(self.corpus_path)
        
    def ingest_chunks(self, chunks: list[dict]):
        print(f"Ingesting {len(chunks)} chunks into Hybrid Retrieval Engine...")
        self.bm25.add_chunks(chunks)
        self.vector.add_chunks(chunks)
        
    def _reciprocal_rank_fusion(self, bm25_results, vector_results, k=60):
        """
        Fuses ranked lists using Reciprocal Rank Fusion (RRF).
        score = 1 / (k + rank)
        """
        rrf_scores = {}
        chunk_map = {}
        
        # Process BM25
        for rank, res in enumerate(bm25_results):
            cid = res["id"]
            chunk_map[cid] = res
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + 1.0 / (k + rank + 1)
            
        # Process Vector
        for rank, res in enumerate(vector_results):
            cid = res["id"]
            chunk_map[cid] = res
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + 1.0 / (k + rank + 1)
            
        # Sort by RRF score
        sorted_chunks = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        
        fused_results = []
        for cid, score in sorted_chunks:
            res = chunk_map[cid]
            res["rrf_score"] = score
            fused_results.append(res)
            
        return fused_results

    def search(self, query: str, top_k: int = 5) -> EvidencePackage:
        bm25_res = self.bm25.search(query, top_k=top_k*2)
        vector_res = self.vector.search(query, top_k=top_k*2)
        
        fused_res = self._reciprocal_rank_fusion(bm25_res, vector_res)
        
        # Take top_k
        final_results = fused_res[:top_k]
        
        # Convert to Pydantic models
        chunks = []
        for r in final_results:
            chunks.append(RetrievedChunk(
                chunk_id=r["id"],
                document_id=r["document_id"],
                text=r["text"],
                section=r.get("section"),
                title=r.get("title"),
                authors=r.get("authors", []),
                year=r.get("year"),
                score=r["rrf_score"],
                retrieval_method="hybrid_rrf"
            ))
            
        return EvidencePackage(
            query=query,
            chunks=chunks,
            metadata={
                "bm25_results_count": len(bm25_res),
                "vector_results_count": len(vector_res)
            }
        )
