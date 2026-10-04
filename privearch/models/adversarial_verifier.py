"""Adversarial Verifier: The 0.5B Decision Auditor in the RLCD Architecture."""

import re
import json
from typing import List, Dict, Any, Tuple
from privearch.schemas import (
    ScoredChunk,
    AtomicClaim,
    VerificationStatus,
    VerificationAudit,
)
from privearch.models.client import LocalModelClient


CLAIM_AUDIT_SYSTEM_PROMPT = """You are Privearch OS Adversarial Verifier, an uncompromising scientific auditor.
Your job is to rigorously verify whether a generated claim is supported by the source literature passage.

Verification Statuses:
- "VERIFIED": The source passage explicitly and directly supports this claim.
- "UNSUPPORTED": The claim makes assertions, numbers, or conclusions NOT present in the source passage (hallucination).
- "CONTRADICTED": The source passage directly disputes or states the opposite of the claim.
- "PARTIAL": Supported in part, but omits critical constraints or extrapolates.

Output ONLY a JSON object:
{
  "status": "VERIFIED" | "UNSUPPORTED" | "CONTRADICTED" | "PARTIAL",
  "evidence_quote": "Exact verbatim excerpt from source, or empty if unsupported",
  "confidence": 0.95,
  "critique": "Brief explanation of verification verdict"
}
"""


class AdversarialVerifier:
    """
    RLCD Decision Component:
    Audits the 4B synthesis against the retrieved PDF chunks, identifying hallucinations.
    """
    def __init__(self, client: LocalModelClient, model_name: str = "qwen2.5:0.5b"):
        self.client = client
        self.model_name = model_name

    def audit(
        self,
        synthesis_text: str,
        retrieved_chunks: List[ScoredChunk]
    ) -> Tuple[VerificationAudit, str]:
        """
        Deconstructs synthesis into claims, verifies each against source chunks,
        and generates an annotated text highlighting unsupported assertions.
        """
        # 1. Extract atomic claims from the synthesized text
        raw_claims = self._extract_atomic_claims(synthesis_text)
        if not raw_claims:
            audit = VerificationAudit(
                total_claims=0,
                verified_count=0,
                unsupported_count=0,
                grounding_score=100.0,
                overall_verdict="SAFE (NO FACTUAL CLAIMS DETECTED)",
                audit_summary="No discrete factual claims required auditing."
            )
            return audit, synthesis_text

        # Map citation indices to chunk text
        chunks_map: Dict[int, ScoredChunk] = {
            i: sc for i, sc in enumerate(retrieved_chunks, start=1)
        }

        audited_claims: List[AtomicClaim] = []
        verified_count = 0
        unsupported_count = 0
        contradicted_count = 0

        # Audit each claim
        for claim_id, (sentence, cited_indices) in enumerate(raw_claims, start=1):
            claim = self._verify_single_claim(
                claim_id=claim_id,
                claim_text=sentence,
                cited_indices=cited_indices,
                chunks_map=chunks_map,
                all_chunks=retrieved_chunks
            )
            audited_claims.append(claim)

            if claim.status == VerificationStatus.VERIFIED:
                verified_count += 1
            elif claim.status == VerificationStatus.CONTRADICTED:
                contradicted_count += 1
            elif claim.status == VerificationStatus.UNSUPPORTED:
                unsupported_count += 1
            elif claim.status == VerificationStatus.PARTIAL:
                verified_count += 0.5  # partial weight

        total = len(audited_claims)
        grounding_score = round((verified_count / total) * 100.0, 1) if total > 0 else 100.0

        if contradicted_count > 0:
            verdict = "CRITICAL: CONTRADICTION DETECTED"
        elif unsupported_count > 0:
            verdict = "CAUTION: UNVERIFIED CLAIMS FLAGGED"
        else:
            verdict = "VERIFIED: 100% GROUNDED IN LITERATURE"

        summary = (
            f"Audited {total} factual claims against {len(retrieved_chunks)} source chunks. "
            f"Grounding score: {grounding_score}%. "
            f"{int(verified_count)} verified, {unsupported_count} unsupported, {contradicted_count} contradictions."
        )

        audit = VerificationAudit(
            total_claims=total,
            verified_count=int(verified_count),
            unsupported_count=unsupported_count,
            contradicted_count=contradicted_count,
            grounding_score=grounding_score,
            overall_verdict=verdict,
            claims=audited_claims,
            audit_summary=summary
        )

        annotated_text = self._build_annotated_synthesis(synthesis_text, audited_claims)
        return audit, annotated_text

    def _extract_atomic_claims(self, text: str) -> List[Tuple[str, List[int]]]:
        """Split synthesis into factual claim sentences with parsed citation indices."""
        # Remove markdown headers and empty lines
        lines = [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith('#')]
        flat_text = " ".join(lines)

        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9])', flat_text)
        claims = []

        for s in sentences:
            clean = s.strip()
            # Must have scientific substance (at least 6 words)
            if len(clean.split()) < 6:
                continue

            # Extract citations like [1], [2], [1, 2]
            cites = [int(m) for m in re.findall(r'\[(\d+)\]', clean)]
            claims.append((clean, cites))

        return claims

    def _verify_single_claim(
        self,
        claim_id: int,
        claim_text: str,
        cited_indices: List[int],
        chunks_map: Dict[int, ScoredChunk],
        all_chunks: List[ScoredChunk]
    ) -> AtomicClaim:
        """Audit a single claim against cited or top retrieved chunks."""
        # Determine source context
        relevant_chunks: List[ScoredChunk] = []
        if cited_indices:
            for idx in cited_indices:
                if idx in chunks_map:
                    relevant_chunks.append(chunks_map[idx])
        if not relevant_chunks and all_chunks:
            # Fallback to top 2 chunks
            relevant_chunks = all_chunks[:2]

        if not relevant_chunks:
            return AtomicClaim(
                claim_id=claim_id,
                text=claim_text,
                status=VerificationStatus.UNSUPPORTED,
                cited_chunk_indices=cited_indices,
                confidence=0.99,
                critique="No retrieved source text available to verify claim."
            )

        # Combine text of candidate chunks
        source_context = "\n---\n".join([
            f"[Passage {sc.final_rank} (Doc: {sc.chunk.doc_name}, Page: {sc.chunk.page_num})]: {sc.chunk.text}"
            for sc in relevant_chunks
        ])

        # For primary claims (1-3), run full 0.5B model LLM audit; for remaining, use fast deterministic overlap
        if claim_id <= 3:
            prompt = (
                f"SOURCE PASSAGES:\n{source_context}\n\n"
                f"CLAIM TO VERIFY:\n\"{claim_text}\"\n\n"
                f"JSON VERDICT:"
            )

            try:
                raw_output = self.client.generate(
                    model=self.model_name,
                    prompt=prompt,
                    system=CLAIM_AUDIT_SYSTEM_PROMPT,
                    temperature=0.05,
                    max_tokens=150
                )
                parsed = self._parse_verdict(raw_output)
                if parsed:
                    status, quote, conf, critique = parsed
                    best_sc = relevant_chunks[0]
                    return AtomicClaim(
                        claim_id=claim_id,
                        text=claim_text,
                        status=status,
                        cited_chunk_indices=cited_indices,
                        evidence_quote=quote,
                        source_doc=best_sc.chunk.doc_name,
                        source_page=best_sc.chunk.page_num,
                        confidence=conf,
                        critique=critique
                    )
            except Exception:
                pass

        # Robust deterministic fallback: N-gram & keyword overlap verification
        return self._rule_based_audit(claim_id, claim_text, cited_indices, relevant_chunks)

    def _parse_verdict(self, raw: str) -> Any:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
                status_str = data.get("status", "UNSUPPORTED").upper()
                if status_str not in [s.value for s in VerificationStatus]:
                    status_str = "UNSUPPORTED"
                return (
                    VerificationStatus(status_str),
                    data.get("evidence_quote", ""),
                    float(data.get("confidence", 0.85)),
                    data.get("critique", "Model audit completed.")
                )
            except Exception:
                pass
        return None

    def _rule_based_audit(
        self,
        claim_id: int,
        claim_text: str,
        cited_indices: List[int],
        relevant_chunks: List[ScoredChunk]
    ) -> AtomicClaim:
        """Deterministic lexical & numerical overlap auditor."""
        clean_claim = re.sub(r'\[\d+\]', '', claim_text).lower()
        claim_words = set(re.findall(r'\b[a-zA-Z0-9_\-\.]{3,}\b', clean_claim))
        
        # Check numbers explicitly (e.g. 298, 1.013, 100, 0.05)
        claim_numbers = set(re.findall(r'\b\d+(?:\.\d+)?\b', clean_claim))

        best_overlap = 0.0
        best_quote = ""
        best_sc = relevant_chunks[0]
        number_mismatch = False

        for sc in relevant_chunks:
            chunk_lower = sc.chunk.text.lower()
            chunk_words = set(re.findall(r'\b[a-zA-Z0-9_\-\.]{3,}\b', chunk_lower))
            chunk_numbers = set(re.findall(r'\b\d+(?:\.\d+)?\b', chunk_lower))

            if claim_numbers and not claim_numbers.issubset(chunk_numbers):
                number_mismatch = True

            intersection = claim_words.intersection(chunk_words)
            overlap = len(intersection) / len(claim_words) if claim_words else 0.0

            if overlap > best_overlap:
                best_overlap = overlap
                best_sc = sc
                # Find matching sentence for evidence quote
                for sent in sc.chunk.text.split('.'):
                    if any(w in sent.lower() for w in list(intersection)[:3]):
                        best_quote = sent.strip() + "."
                        break

        # Verification threshold
        if number_mismatch and claim_numbers:
            status = VerificationStatus.UNSUPPORTED
            critique = "Numerical value in claim not found in cited source text."
            conf = 0.90
        elif best_overlap >= 0.65:
            status = VerificationStatus.VERIFIED
            critique = f"Strong lexical and semantic support in text ({int(best_overlap*100)}% term alignment)."
            conf = 0.92
        elif best_overlap >= 0.40:
            status = VerificationStatus.PARTIAL
            critique = "Partial alignment with source passage; some terms ungrounded."
            conf = 0.75
        else:
            status = VerificationStatus.UNSUPPORTED
            critique = "Insufficient evidence in source passage (Hallucination risk)."
            conf = 0.88

        return AtomicClaim(
            claim_id=claim_id,
            text=claim_text,
            status=status,
            cited_chunk_indices=cited_indices,
            evidence_quote=best_quote or best_sc.chunk.text[:120] + "...",
            source_doc=best_sc.chunk.doc_name,
            source_page=best_sc.chunk.page_num,
            confidence=conf,
            critique=critique
        )

    def _build_annotated_synthesis(self, text: str, claims: List[AtomicClaim]) -> str:
        """Inject warning highlights and verified stamps into synthesis text."""
        annotated = text
        for c in claims:
            if c.status == VerificationStatus.UNSUPPORTED:
                # Add alert badge
                clean_text = c.text
                badge = f"\n> ⚠️ **[AUDIT: UNSUPPORTED CLAIM]** {c.critique}\n"
                if clean_text in annotated:
                    annotated = annotated.replace(clean_text, f"{clean_text} ⚠️{badge}")
            elif c.status == VerificationStatus.CONTRADICTED:
                clean_text = c.text
                badge = f"\n> ❌ **[AUDIT: CONTRADICTION]** {c.critique}\n"
                if clean_text in annotated:
                    annotated = annotated.replace(clean_text, f"{clean_text} ❌{badge}")
        return annotated
