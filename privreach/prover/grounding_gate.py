"""
Zero-Hallucination Grounding Gate.

Acts as the deterministic gatekeeper between stochastic LLM synthesis
and the end-user researcher. Strips or stigmatizes any factual assertion
that cannot be proven from vault document spans.
"""

from typing import List, Dict, Any, Optional
import uuid

from privreach.prover.claim_decomposer import ClaimDecomposer, AtomicClaim
from privreach.prover.span_matcher import SpanMatcher, SpanMatchResult
from privreach.prover.confidence_report import ProofReport, ClaimVerification, VerificationVerdict


class GroundingGate:
    """
    Enforces deterministic zero-hallucination compliance.
    """

    def __init__(
        self,
        strict_mode: bool = True,
        fuzzy_threshold: float = 0.70,
        min_grounding_ratio: float = 0.80,
    ):
        self.strict_mode = strict_mode
        self.decomposer = ClaimDecomposer()
        self.span_matcher = SpanMatcher(fuzzy_threshold=fuzzy_threshold)
        self.min_grounding_ratio = min_grounding_ratio

    def verify_and_gate(
        self,
        llm_response_text: str,
        evidence_chunks: List[Any],
    ) -> ProofReport:
        """
        Decomposes response into atomic claims, verifies each against evidence,
        and constructs the ProofReport with verified output text.
        """
        report_id = f"proof_{uuid.uuid4().hex[:8]}"

        if not llm_response_text.strip():
            return ProofReport(
                report_id=report_id,
                total_claims=0,
                verified_claims=0,
                unsupported_claims=0,
                grounding_ratio=1.0,
                is_strictly_verified=True,
                original_text="",
                verified_text="",
                claims=[],
            )

        claims = self.decomposer.decompose(llm_response_text)
        if not claims:
            # No atomic claims parsed
            return ProofReport(
                report_id=report_id,
                total_claims=0,
                verified_claims=0,
                unsupported_claims=0,
                grounding_ratio=1.0,
                is_strictly_verified=True,
                original_text=llm_response_text,
                verified_text=llm_response_text,
                claims=[],
            )

        verified_count = 0
        unsupported_count = 0
        claim_verifications: List[ClaimVerification] = []
        verified_sentences: List[str] = []

        for atomic in claims:
            if not atomic.is_factual_candidate:
                # Retain non-factual framing without penalty
                verified_sentences.append(atomic.original_sentence)
                continue

            match_res = self.span_matcher.match_claim(atomic.normalized_text, evidence_chunks)

            if match_res.is_matched:
                verdict = (
                    VerificationVerdict.VERIFIED
                    if match_res.match_type == "exact"
                    else VerificationVerdict.PARTIALLY_SUPPORTED
                )
                confidence = match_res.similarity_score
                verified_count += 1
                verified_sentences.append(atomic.original_sentence)
                audit_note = (
                    f"Grounded in {match_res.source_doc} (page {match_res.source_page})"
                )
            else:
                verdict = VerificationVerdict.UNSUPPORTED
                confidence = 0.0
                unsupported_count += 1
                audit_note = "No verifiable span found in evidence repository"

                if not self.strict_mode:
                    # In non-strict mode, flag the sentence rather than dropping it
                    verified_sentences.append(f"{atomic.original_sentence} [UNSUPPORTED CLAIM]")

            claim_verifications.append(
                ClaimVerification(
                    claim_id=atomic.claim_id,
                    claim_text=atomic.original_sentence,
                    verdict=verdict,
                    confidence=confidence,
                    attribution=match_res,
                    audit_notes=audit_note,
                )
            )

        total_factual = verified_count + unsupported_count
        grounding_ratio = round(verified_count / total_factual, 4) if total_factual > 0 else 1.0
        is_strictly_verified = unsupported_count == 0

        verified_text = " ".join(verified_sentences).strip()

        return ProofReport(
            report_id=report_id,
            total_claims=total_factual,
            verified_claims=verified_count,
            unsupported_claims=unsupported_count,
            grounding_ratio=grounding_ratio,
            is_strictly_verified=is_strictly_verified,
            original_text=llm_response_text,
            verified_text=verified_text,
            claims=claim_verifications,
        )
