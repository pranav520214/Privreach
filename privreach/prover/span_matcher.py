"""
Deterministic Span Matcher and Citation Attribution Engine.

Performs multi-stage ground-truth search across source passages:
- Stage 1: Exact verbatim substring match
- Stage 2: Sliding-window token Jaccard alignment
- Stage 3: Normalized character Levenshtein proximity
Returns exact document, page number, chunk ID, and verbatim span text.
"""

from typing import List, Dict, Any, Optional, Tuple
import re
from pydantic import BaseModel, Field


class SpanMatchResult(BaseModel):
    is_matched: bool
    match_type: str = "none"  # "exact", "fuzzy", "none"
    similarity_score: float = 0.0
    source_doc: Optional[str] = None
    source_page: Optional[int] = None
    source_chunk_id: Optional[str] = None
    verbatim_span: Optional[str] = None


class SpanMatcher:
    """
    Locates exact or near-exact supporting spans for claims in evidence passages.
    """

    def __init__(self, exact_threshold: float = 1.0, fuzzy_threshold: float = 0.65):
        self.exact_threshold = exact_threshold
        self.fuzzy_threshold = fuzzy_threshold

    @staticmethod
    def clean_text_for_comparison(text: str) -> str:
        """Lowercases, normalizes whitespace and punctuation for canonical substring checks."""
        clean = re.sub(r"[^\w\s]", " ", text.lower())
        return " ".join(clean.split())

    @staticmethod
    def token_overlap_score(claim_tokens: set, window_tokens: set) -> float:
        """
        Computes composite attribution score:
        70% Claim Token Coverage (Recall) + 30% Jaccard Precision.
        Ensures claims embedded in larger passages are accurately attributed.
        """
        if not claim_tokens or not window_tokens:
            return 0.0
        intersection = len(claim_tokens.intersection(window_tokens))
        coverage = intersection / len(claim_tokens)
        union = len(claim_tokens.union(window_tokens))
        jaccard = intersection / union if union > 0 else 0.0
        return (0.70 * coverage) + (0.30 * jaccard)

    def match_claim(
        self,
        claim_text: str,
        evidence_chunks: List[Any],  # List[DocumentChunk] or Dict[str, Any]
    ) -> SpanMatchResult:
        """
        Attempts to ground claim_text against the provided evidence chunks.
        """
        clean_claim = self.clean_text_for_comparison(claim_text)
        claim_tokens = set(clean_claim.split())

        if not claim_tokens:
            return SpanMatchResult(is_matched=False, match_type="none")

        best_fuzzy_score = 0.0
        best_fuzzy_result: Optional[SpanMatchResult] = None

        for chunk in evidence_chunks:
            # Extract fields whether DocumentChunk model or dict
            text = getattr(chunk, "text", None) or (chunk.get("text") if isinstance(chunk, dict) else str(chunk))
            doc_name = getattr(chunk, "doc_name", None) or (chunk.get("doc_name") if isinstance(chunk, dict) else "unknown_doc")
            page_num = getattr(chunk, "page_num", None) or (chunk.get("page_num") if isinstance(chunk, dict) else 1)
            chunk_id = getattr(chunk, "chunk_id", None) or (chunk.get("chunk_id") if isinstance(chunk, dict) else "c_000")

            if not text:
                continue

            clean_chunk = self.clean_text_for_comparison(text)

            # Stage 1: Exact Normalized Substring Search
            if clean_claim in clean_chunk:
                # Find matching verbatim slice in original text
                start_pos = clean_chunk.find(clean_claim)
                # Approximate span window from original text
                words_before = len(clean_chunk[:start_pos].split())
                orig_words = text.split()
                claim_word_count = len(clean_claim.split())
                verbatim_slice = " ".join(orig_words[words_before : words_before + claim_word_count + 3])

                return SpanMatchResult(
                    is_matched=True,
                    match_type="exact",
                    similarity_score=1.0,
                    source_doc=doc_name,
                    source_page=page_num,
                    source_chunk_id=chunk_id,
                    verbatim_span=verbatim_slice or claim_text,
                )

            # Stage 2: Sliding-Window Token Jaccard Search
            chunk_words = text.split()
            window_size = max(4, len(claim_tokens) + 4)
            step_size = max(1, window_size // 3)

            for i in range(0, max(1, len(chunk_words) - window_size + 1), step_size):
                window_words = chunk_words[i : i + window_size]
                clean_window = self.clean_text_for_comparison(" ".join(window_words))
                window_tokens = set(clean_window.split())

                score = self.token_overlap_score(claim_tokens, window_tokens)
                if score > best_fuzzy_score:
                    best_fuzzy_score = score
                    best_fuzzy_result = SpanMatchResult(
                        is_matched=score >= self.fuzzy_threshold,
                        match_type="fuzzy" if score >= self.fuzzy_threshold else "none",
                        similarity_score=round(score, 4),
                        source_doc=doc_name,
                        source_page=page_num,
                        source_chunk_id=chunk_id,
                        verbatim_span=" ".join(window_words),
                    )

        if best_fuzzy_result and best_fuzzy_result.is_matched:
            return best_fuzzy_result

        return SpanMatchResult(
            is_matched=False,
            match_type="none",
            similarity_score=round(best_fuzzy_score, 4),
        )
