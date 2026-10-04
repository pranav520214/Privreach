"""Hybrid Retrieval module fusing Okapi BM25 and Dense FAISS Vector Search with RRF."""
from privearch.retrieval.embeddings import get_embedding_engine
from privearch.retrieval.bm25 import InRamBM25
from privearch.retrieval.faiss_index import InRamVectorIndex
from privearch.retrieval.hybrid_rrf import HybridRRFRetriever

__all__ = ["get_embedding_engine", "InRamBM25", "InRamVectorIndex", "HybridRRFRetriever"]
