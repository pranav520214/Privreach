"""Hybrid Retriever fusing Okapi BM25 and FAISS dense vector search using Reciprocal Rank Fusion (RRF)."""

from typing import List, Dict, Any, Optional
from collections import defaultdict
import numpy as np

from privearch.schemas import DocumentChunk, ScoredChunk
from privearch.retrieval.bm25 import InRamBM25
from privearch.retrieval.faiss_index import InRamVectorIndex
from privearch.retrieval.embeddings import BaseEmbeddingEngine


class HybridRRFRetriever:
    """
    RLCD Logic Component:
    Executes dual-channel retrieval (lexical Okapi BM25 + semantic FAISS),
    then harmonizes candidate lists via Reciprocal Rank Fusion.
    """
    def __init__(
        self,
        bm25_index: InRamBM25,
        vector_index: InRamVectorIndex,
        embedding_engine: BaseEmbeddingEngine,
        rrf_k: int = 60
    ):
        self.bm25 = bm25_index
        self.vector_index = vector_index
        self.embedding_engine = embedding_engine
        self.rrf_k = rrf_k

    def retrieve(
        self,
        query: str,
        lexical_keywords: Optional[List[str]] = None,
        top_k_bm25: int = 12,
        top_k_dense: int = 12,
        top_k_final: int = 6
    ) -> List[ScoredChunk]:
        """
        Fuses BM25 and Dense FAISS ranking.
        """
        # 1. Prepare Lexical Query (enrich with router keywords if provided)
        bm25_query = query
        if lexical_keywords:
            bm25_query = f"{query} {' '.join(lexical_keywords)}"

        # 2. Execute BM25 search
        bm25_results = self.bm25.search(bm25_query, top_k=top_k_bm25)
        # Map: chunk_idx -> (rank, score)
        bm25_ranks: Dict[int, int] = {}
        bm25_scores: Dict[int, float] = {}
        for rank, (idx, score) in enumerate(bm25_results, start=1):
            bm25_ranks[idx] = rank
            bm25_scores[idx] = score

        # 3. Execute Dense Vector search
        query_vector = self.embedding_engine.embed_query(query)
        dense_results = self.vector_index.search(query_vector, top_k=top_k_dense)
        dense_ranks: Dict[int, int] = {}
        dense_scores: Dict[int, float] = {}
        for rank, (idx, score) in enumerate(dense_results, start=1):
            dense_ranks[idx] = rank
            dense_scores[idx] = score

        # 4. Reciprocal Rank Fusion (RRF)
        # RRF_score(d) = 1 / (k + rank_bm25(d)) + 1 / (k + rank_dense(d))
        all_candidate_indices = set(bm25_ranks.keys()).union(set(dense_ranks.keys()))
        rrf_scores: Dict[int, float] = defaultdict(float)

        for idx in all_candidate_indices:
            score = 0.0
            if idx in bm25_ranks:
                score += 1.0 / (self.rrf_k + bm25_ranks[idx])
            if idx in dense_ranks:
                score += 1.0 / (self.rrf_k + dense_ranks[idx])
            rrf_scores[idx] = score

        # Sort candidates descending by RRF score
        sorted_candidates = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        top_selected = sorted_candidates[:top_k_final]

        # 5. Build ScoredChunk list
        scored_chunks: List[ScoredChunk] = []
        for final_rank, (idx, rrf_val) in enumerate(top_selected, start=1):
            chunk = self.bm25.chunks[idx]
            scored_chunks.append(ScoredChunk(
                chunk=chunk,
                bm25_score=bm25_scores.get(idx, 0.0),
                bm25_rank=bm25_ranks.get(idx, None),
                dense_score=dense_scores.get(idx, 0.0),
                dense_rank=dense_ranks.get(idx, None),
                rrf_score=round(rrf_val, 6),
                final_rank=final_rank
            ))

        return scored_chunks
