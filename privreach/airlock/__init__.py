"""
privreach.airlock: Cybersecurity Content Disarm & Reconstruction (CDR) Subsystem.

Responsible for:
- Polyglot payload detection and multi-format collision rejection
- Deep structural PDF sanitization (active content & script stripping)
- Visual flattening (Zero-Trust raster-to-PDF reconstitution)
- Prompt injection and adversarial jailbreak text filtration
- Cryptographic verification receipts for air-gap boundary crossing
"""

from privreach.airlock.polyglot_detector import PolyglotDetector, PolyglotCheckResult
from privreach.airlock.pdf_sanitizer import PDFSanitizer, SanitizationReport
from privreach.airlock.visual_flattener import VisualFlattener
from privreach.airlock.prompt_injection_filter import PromptInjectionFilter, InjectionCheckResult
from privreach.airlock.cdr_pipeline import CDRPipeline, CDRResult

__all__ = [
    "PolyglotDetector",
    "PolyglotCheckResult",
    "PDFSanitizer",
    "SanitizationReport",
    "VisualFlattener",
    "PromptInjectionFilter",
    "InjectionCheckResult",
    "CDRPipeline",
    "CDRResult",
]
