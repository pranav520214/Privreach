"""System configuration for Privearch local OS."""

from dataclasses import dataclass, field
from typing import List
import os

@dataclass
class PrivearchConfig:
    # Service Endpoints
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")

    # Dual-Model Brain-Trust Models
    # 0.5B tiny model for routing & verification
    router_model: str = os.getenv("PRIVEARCH_ROUTER_MODEL", "qwen2.5:0.5b")
    router_fallbacks: List[str] = field(default_factory=lambda: ["qwen2.5:0.5b", "llama3.2:1b", "qwen2.5-coder:1.5b-instruct"])

    # 1B-4B heavy model for deep scientific synthesis
    synthesis_model: str = os.getenv("PRIVEARCH_SYNTHESIS_MODEL", "google/gemma-3-1b-it")
    synthesis_fallbacks: List[str] = field(default_factory=lambda: ["google/gemma-3-1b-it", "gemma3:1b", "qwen2.5-coder:3b", "medgemma:4b"])

    # 0.5B adversarial verifier
    verifier_model: str = os.getenv("PRIVEARCH_VERIFIER_MODEL", "qwen2.5:0.5b")
    verifier_fallbacks: List[str] = field(default_factory=lambda: ["qwen2.5:0.5b", "llama3.2:1b"])

    # Embedding engine: "cpu_minilm" (runs on CPU to leave 100% of 4GB VRAM for LLM) or "ollama"
    embedding_backend: str = "cpu_minilm"
    cpu_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ollama_embedding_model: str = "qwen3-embedding:0.6b"

    # Chunking & Semantic Partitioning
    chunk_size_words: int = 150
    chunk_overlap_words: int = 30
    min_chunk_words: int = 20

    # Retrieval Tuning
    bm25_k1: float = 1.5
    bm25_b: float = 0.75
    top_k_bm25: int = 12
    top_k_dense: int = 12
    top_k_final: int = 6
    rrf_k: int = 60

    # Verification & Hallucination Controls
    audit_high_risk_only: bool = False  # Audit all academic queries for maximum safety
    strict_unsupported_highlighting: bool = True
    grounding_confidence_threshold: float = 0.70

    # Local Hardware Limits
    max_vram_limit_gb: float = 4.0
    zero_trust_airgap: bool = True  # Reject any external outbound requests

DEFAULT_CONFIG = PrivearchConfig()
