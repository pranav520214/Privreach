"""
Deterministic Claim Decomposer.

Splits multi-sentence LLM synthesis text into atomic, testable claims
while stripping conversational filler and non-factual discourse markers.
"""

from typing import List
import re
from pydantic import BaseModel, Field


class AtomicClaim(BaseModel):
    """An individual verifiable claim extracted from an LLM response."""
    claim_id: str
    original_sentence: str
    normalized_text: str
    is_factual_candidate: bool = True


DISCOURSE_FILLERS = [
    r"^in\s+conclusion\b",
    r"^to\s+summarize\b",
    r"^overall\b",
    r"^furthermore\b",
    r"^in\s+addition\b",
    r"^based\s+on\s+the\s+(?:provided\s+)?(?:context|documents?|records?)\b",
    r"^according\s+to\s+the\s+research\b",
    r"^as\s+mentioned\s+above\b",
    r"^note\s+that\b",
    r"^it\s+is\s+worth\s+noting\s+that\b",
    r"^here\s+is\s+(?:the\s+)?(?:information|summary|breakdown)\b",
]


class ClaimDecomposer:
    """
    Parses unstructured LLM response text into discrete atomic claims.
    """

    def __init__(self, min_claim_length: int = 15):
        self.min_claim_length = min_claim_length

    def split_sentences(self, text: str) -> List[str]:
        """
        Splits text on sentence boundaries, list bullets, and paragraph breaks.
        """
        # Clean markdown headers, list symbols, and blockquotes
        cleaned_lines = []
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
            # Strip markdown list markers (- , * , 1. , etc.)
            line = re.sub(r"^(?:[-*+]|\d+\.)\s+", "", line)
            # Strip markdown header hashes
            line = re.sub(r"^#+\s+", "", line)
            cleaned_lines.append(line)

        raw_joined = " ".join(cleaned_lines)

        # Split on sentence ending punctuation (., !, ?) respecting abbreviations like e.g., i.e.
        # Simple robust regex for sentence breaking
        sentence_candidates = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", raw_joined)

        clean_sentences: List[str] = []
        for s in sentence_candidates:
            s_clean = s.strip()
            if len(s_clean) >= self.min_claim_length:
                clean_sentences.append(s_clean)

        return clean_sentences

    def normalize_claim(self, sentence: str) -> str:
        """
        Removes conversational discourse markers and normalizes whitespace/punctuation.
        """
        norm = sentence.strip()
        # Remove bold/italic markdown
        norm = re.sub(r"[*_`]", "", norm)

        # Remove leading discourse filler
        for filler in DISCOURSE_FILLERS:
            norm = re.sub(filler, "", norm, flags=re.IGNORECASE).strip()
            norm = re.sub(r"^,\s*", "", norm).strip()

        return norm

    def decompose(self, text: str) -> List[AtomicClaim]:
        """
        Decomposes a response text into a list of AtomicClaim instances.
        """
        sentences = self.split_sentences(text)
        claims: List[AtomicClaim] = []

        for idx, sent in enumerate(sentences):
            norm = self.normalize_claim(sent)
            # Check if sentence is genuinely factual or just a rhetorical framing
            is_factual = len(norm.split()) >= 4 and not norm.endswith("?")

            claims.append(
                AtomicClaim(
                    claim_id=f"claim_{idx:03d}",
                    original_sentence=sent,
                    normalized_text=norm,
                    is_factual_candidate=is_factual,
                )
            )

        return claims
