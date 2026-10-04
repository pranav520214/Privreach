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

class EvidenceType(str, Enum):
    DOCUMENT_PAGE = "DOCUMENT_PAGE"
    VIDEO_TIMECODE = "VIDEO_TIMECODE"
    AUDIO_TRANSCRIPT = "AUDIO_TRANSCRIPT"
    COMPUTATION_RESULT = "COMPUTATION_RESULT"


class EvidenceChunk(BaseModel):
    """Unified multi-modal evidence chunk across documents, video, and audio."""
    chunk_id: str
    source_name: str
    evidence_type: EvidenceType = EvidenceType.DOCUMENT_PAGE
    page_num: Optional[int] = None
    timestamp_start: Optional[float] = None  # seconds
    timestamp_end: Optional[float] = None    # seconds
    speaker_id: Optional[str] = None
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ToolCallRequest(BaseModel):
    """Request to invoke a deterministic tool adapter."""
    tool_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    purpose: str = ""


class ToolCallResult(BaseModel):
    """Result returned by a deterministic tool adapter."""
    tool_name: str
    success: bool
    output: Any = None
    stdout: str = ""
    stderr: str = ""
    execution_time_ms: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CalculationVerification(BaseModel):
    """Deterministic scientific calculation audit record."""
    equation_latex: str = ""
    target_variable: str = ""
    variables: Dict[str, Any] = Field(default_factory=dict)
    units: Dict[str, str] = Field(default_factory=dict)
    model_predicted_value: Optional[str] = None
    deterministic_computed_value: Optional[str] = None
    is_verified: bool = False
    absolute_error: Optional[float] = None
    relative_error: Optional[float] = None
    verification_status: VerificationStatus = VerificationStatus.UNSUPPORTED
    verification_details: str = ""
    code_executed: str = ""


class ArtifactType(str, Enum):
    CALCULATION = "CALCULATION"
    PLOT_2D = "PLOT_2D"
    DATASET = "DATASET"
    MODEL_3D = "MODEL_3D"
    VIDEO_EXPLAINER = "VIDEO_EXPLAINER"
    REPORT_PDF = "REPORT_PDF"
    SLIDES_PPTX = "SLIDES_PPTX"


class ArtifactRecord(BaseModel):
    """Tracked artifact with complete provenance linkage."""
    artifact_id: str
    artifact_type: ArtifactType
    name: str
    file_path: str
    created_at: float
    description: str = ""
    provenance: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


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
    calculations: List[CalculationVerification] = Field(default_factory=list)
    artifacts: List[ArtifactRecord] = Field(default_factory=list)
    tool_executions: List[ToolCallResult] = Field(default_factory=list)

