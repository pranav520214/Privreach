"""
Deterministic Prompt Injection and Adversarial Text Filter.

Detects and defangs indirect prompt injection attempts embedded within
harvested research papers, documents, and web texts before LLM processing.
"""

from typing import List, Dict, Tuple, Optional
import re
from pydantic import BaseModel, Field


class InjectionCheckResult(BaseModel):
    is_safe: bool
    risk_score: float  # 0.0 (safe) to 1.0 (malicious)
    detected_patterns: List[str] = Field(default_factory=list)
    sanitized_text: str = ""


# Compiled regex patterns for indirect prompt injections and jailbreaks
INJECTION_SIGNATURES: List[Tuple[re.Pattern, str, float]] = [
    # (compiled_regex, description, severity_weight)
    (
        re.compile(r"ignore\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions?|prompts?|directives?)", re.I),
        "Instruction override directive ('ignore previous instructions')",
        0.95,
    ),
    (
        re.compile(r"(?:disregard|forget)\s+(?:all\s+)?(?:previous|prior)\s+(?:rules?|guidelines?)", re.I),
        "Rule disregard directive",
        0.90,
    ),
    (
        re.compile(r"(?:you\s+are\s+now|act\s+as)\s+(?:an?\s+unrestricted|a\s+hacked|DAN|jailbroken)", re.I),
        "Persona hijacking / DAN jailbreak attempt",
        0.95,
    ),
    (
        re.compile(r"<\s*\|?\s*(?:im_start|im_end|system|user|assistant)\s*\|?\s*>", re.I),
        "ChatML delimiter injection",
        0.98,
    ),
    (
        re.compile(r"\[\s*(?:system|system_message|inst|instruct)\s*\]", re.I),
        "System prompt bracket delimiter injection",
        0.85,
    ),
    (
        re.compile(r"system\s*:\s*(?:you\s+must|override|always|do\s+not\s+tell)", re.I),
        "Simulated system turn injection",
        0.88,
    ),
    (
        re.compile(r"(?:do\s+not\s+reveal|keep\s+this\s+secret|exfiltrate|send\s+to\s+https?://)", re.I),
        "Data exfiltration or secrecy directive",
        0.80,
    ),
    (
        re.compile(r"```(?:system|admin|root)", re.I),
        "Code fence privileged environment escape",
        0.75,
    ),
]

ZERO_WIDTH_CHARS = [
    "\u200b",  # zero-width space
    "\u200c",  # zero-width non-joiner
    "\u200d",  # zero-width joiner
    "\ufeff",  # zero-width no-break space
    "\u2060",  # word joiner
    "\u200e",  # left-to-right mark
    "\u200f",  # right-to-left mark
]


class PromptInjectionFilter:
    """
    Scans and cleans text to neutralize adversarial LLM prompt manipulation.
    """

    def __init__(self, risk_threshold: float = 0.50):
        self.risk_threshold = risk_threshold

    def clean_zero_width_chars(self, text: str) -> str:
        """Strips invisible Unicode zero-width characters used for steganography or filter evasion."""
        clean = text
        for zwc in ZERO_WIDTH_CHARS:
            clean = clean.replace(zwc, "")
        return clean

    def scan(self, text: str) -> InjectionCheckResult:
        """
        Evaluates text for indirect prompt injections and generates sanitized copy.
        """
        if not text:
            return InjectionCheckResult(is_safe=True, risk_score=0.0, detected_patterns=[], sanitized_text="")

        normalized_text = self.clean_zero_width_chars(text)
        detected_patterns: List[str] = []
        max_severity = 0.0

        for pattern, desc, severity in INJECTION_SIGNATURES:
            if pattern.search(normalized_text):
                detected_patterns.append(desc)
                if severity > max_severity:
                    max_severity = severity

        # Calculate composite risk score
        count_penalty = min(0.30, len(detected_patterns) * 0.10)
        composite_risk = min(1.0, max_severity + count_penalty)

        is_safe = composite_risk < self.priority_risk_threshold if hasattr(self, "priority_risk_threshold") else (composite_risk < self.risk_threshold)

        # Defang detected matches in sanitized copy
        sanitized = normalized_text
        for pattern, desc, _ in INJECTION_SIGNATURES:
            sanitized = pattern.sub("[DEFANGED_INJECTION_DIRECTIVE]", sanitized)

        return InjectionCheckResult(
            is_safe=is_safe,
            risk_score=round(composite_risk, 4),
            detected_patterns=detected_patterns,
            sanitized_text=sanitized,
        )
