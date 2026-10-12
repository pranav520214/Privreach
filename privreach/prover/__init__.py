"""
privreach.prover: Zero-Hallucination Proof Engine Subsystem.

Responsible for:
- Deterministic claim decomposition of LLM synthesis outputs
- Exact substring span matching and fuzzy n-gram token attribution
- Verification verdict stamping (VERIFIED vs. UNSUPPORTED)
- Strict grounding gate enforcement and claim stripping
- Cryptographic proof audit reports
"""

from privreach.prover.claim_decomposer import ClaimDecomposer, AtomicClaim
from privreach.prover.span_matcher import SpanMatcher, SpanMatchResult
from privreach.prover.confidence_report import ProofReport, ClaimVerification, VerificationVerdict
from privreach.prover.grounding_gate import GroundingGate

__all__ = [
    "ClaimDecomposer",
    "AtomicClaim",
    "SpanMatcher",
    "SpanMatchResult",
    "ProofReport",
    "ClaimVerification",
    "VerificationVerdict",
    "GroundingGate",
]
