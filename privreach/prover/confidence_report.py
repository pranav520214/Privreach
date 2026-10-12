"""
Cryptographic Proof and Grounding Audit Schemas.
"""

from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from privreach.prover.span_matcher import SpanMatchResult


class VerificationVerdict(str, Enum):
    VERIFIED = "VERIFIED"
    UNSUPPORTED = "UNSUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"


class ClaimVerification(BaseModel):
    """Result of an individual claim verification pass."""
    claim_id: str
    claim_text: str
    verdict: VerificationVerdict
    confidence: float
    attribution: Optional[SpanMatchResult] = None
    audit_notes: str = ""


class ProofReport(BaseModel):
    """Holistic audit report proving truthfulness and absence of hallucinations."""
    report_id: str
    timestamp_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    total_claims: int = 0
    verified_claims: int = 0
    unsupported_claims: int = 0
    grounding_ratio: float = 0.0  # verified_claims / total_claims
    is_strictly_verified: bool = False  # True if grounding_ratio == 1.0
    original_text: str = ""
    verified_text: str = ""  # Text with unsupported claims stripped or flagged
    claims: List[ClaimVerification] = Field(default_factory=list)
