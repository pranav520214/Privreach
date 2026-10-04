"""Pydantic schemas for Privearch RLCD pipeline."""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    CRITICAL = "CRITICAL"  # Toxicity, explosive safety, medical dosing, structural failure
    HIGH = "HIGH"          # Mechanistic chemistry, thermodynamic equilibria, physiological pathways
    MEDIUM = "MEDIUM"      # Literature synthesis, standard definitions, general reactions
    LOW = "LOW"            # General knowledge, syntax, index browsing


class TaskType(str, Enum):
    LITERATURE_REVIEW = "LITERATURE_REVIEW"
    MECHANISTIC_SYNTHESIS = "MECHANISTIC_SYNTHESIS"
    FACT_CHECK = "FACT_CHECK"
    SAFETY_AUDIT = "SAFETY_AUDIT"
    CALCULATION_DERIVATION = "CALCULATION_DERIVATION"
    DEFINITION_EXTRACTION = "DEFINITION_EXTRACTION"


class QueryAnalysis(BaseModel):
    """Output schema produced by the 0.5B Router."""
    risk_level: RiskLevel = Field(
        default=RiskLevel.MEDIUM,
        description="Hazard or hallucination risk level"
    )
    task_type: TaskType = Field(
        default=TaskType.LITERATURE_REVIEW,
        description="Specific scientific analytical task"
    )
    scientific_domain: str = Field(
        default="Chemistry / General Science",
        description="Primary scientific domain"
    )
    key_entities: List[str] = Field(
        default_factory=list,
        description="Chemicals, formulas, laws, theorems or biological markers"
    )
    lexical_keywords: List[str] = Field(
        default_factory=list,
        description="Exact terms for Okapi BM25 keyword matching"
    )
    semantic_queries: List[str] = Field(
        default_factory=list,
        description="Paraphrased queries for dense vector FAISS retrieval"
    )
    adversarial_audit_required: bool = Field(
        default=True,
        description="Whether adversarial claim verification should be executed"
    )
    analysis_rationale: str = Field(
        default="",
        description="Short reason for risk level and retrieval focus"
    )


class DocumentChunk(BaseModel):
    """A semantic fragment of an ingested scientific PDF."""
    chunk_id: str
    doc_name: str
    page_num: int
    section_header: str = ""
    text: str
    char_count: int = 0
    word_count: int = 0


class ScoredChunk(BaseModel):
    """Retrieved chunk tagged with BM25, FAISS, and RRF scores."""
    chunk: DocumentChunk
    bm25_score: float = 0.0
    bm25_rank: Optional[int] = None
    dense_score: float = 0.0
    dense_rank: Optional[int] = None
    rrf_score: float = 0.0
    final_rank: int = 0


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"          # Direct evidence present in source
    UNSUPPORTED = "UNSUPPORTED"    # Claim not backed by cited or retrieved text (Hallucination risk)
    CONTRADICTED = "CONTRADICTED"  # Direct contradiction with source PDF text
    PARTIAL = "PARTIAL"            # Partially true but missing key conditions / caveats


class AtomicClaim(BaseModel):
    """Single factual assertion extracted from the 4B synthesis."""
    claim_id: int
    text: str
    status: VerificationStatus = VerificationStatus.UNSUPPORTED
    cited_chunk_indices: List[int] = Field(default_factory=list)
    evidence_quote: str = ""
    source_doc: str = ""
    source_page: Optional[int] = None
    confidence: float = 0.0
    critique: str = ""


class VerificationAudit(BaseModel):
    """Output of the 0.5B Adversarial Verifier audit."""
    total_claims: int = 0
    verified_count: int = 0
    unsupported_count: int = 0
    contradicted_count: int = 0
    grounding_score: float = 0.0  # Percentage (0-100%)
    overall_verdict: str = "SAFE & GROUNDED"
    claims: List[AtomicClaim] = Field(default_factory=list)
    audit_summary: str = ""


class PrivearchReport(BaseModel):
    """Complete structured response from the Privearch OS."""
    query: str
    query_analysis: QueryAnalysis
    retrieved_chunks: List[ScoredChunk]
    raw_synthesis: str
    verification: VerificationAudit
    annotated_synthesis: str
    execution_stats: Dict[str, Any] = Field(default_factory=dict)
