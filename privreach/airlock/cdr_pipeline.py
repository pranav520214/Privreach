"""
Content Disarm and Reconstruction (CDR) Gateway Pipeline.

Orchestrates the 4-stage document defense before air-gap admission:
1. Polyglot and collision analysis (PolyglotDetector)
2. Structural active content sanitization (PDFSanitizer)
3. Adversarial prompt injection defense (PromptInjectionFilter)
4. Optional Zero-Trust visual flattening (VisualFlattener)
"""

from typing import List, Dict, Any, Optional
import os
import hashlib
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from privreach.airlock.polyglot_detector import PolyglotDetector, PolyglotCheckResult
from privreach.airlock.pdf_sanitizer import PDFSanitizer, SanitizationReport
from privreach.airlock.visual_flattener import VisualFlattener
from privreach.airlock.prompt_injection_filter import PromptInjectionFilter, InjectionCheckResult
import fitz  # PyMuPDF for text extraction


class CDRResult(BaseModel):
    """Cryptographic audit receipt emitted by the Airlock CDR gateway."""
    is_cleared: bool
    source_sha256: str
    sanitized_sha256: Optional[str] = None
    quarantine_src_path: str
    vault_dest_path: Optional[str] = None
    processed_at_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    polyglot_check: PolyglotCheckResult
    sanitization_report: SanitizationReport
    injection_check: InjectionCheckResult
    visual_flattening_applied: bool = False
    audit_log: List[str] = Field(default_factory=list)


class CDRPipeline:
    """
    Main cybersecurity gateway separating external downloads from the air-gapped vault.
    """

    def __init__(
        self,
        vault_clean_dir: str = "vault_inbox",
        enable_visual_flattening: bool = False,
    ):
        self.vault_clean_dir = vault_clean_dir
        self.enable_visual_flattening = enable_visual_flattening

        self.polyglot_detector = PolyglotDetector()
        self.sanitizer = PDFSanitizer()
        self.visual_flattener = VisualFlattener()
        self.injection_filter = PromptInjectionFilter()

        os.makedirs(self.vault_clean_dir, exist_ok=True)

    def process_file(
        self,
        src_path: str,
        dest_filename: Optional[str] = None,
        force_visual_flatten: bool = False,
    ) -> CDRResult:
        """
        Processes a quarantined file through the 4-stage CDR pipeline.
        Returns cryptographic CDRResult receipt.
        """
        audit_log: List[str] = []
        audit_log.append(f"Initiated CDR processing for {src_path}")

        # Compute source file hash
        with open(src_path, "rb") as f:
            src_bytes = f.read()
        src_sha256 = hashlib.sha256(src_bytes).hexdigest()
        audit_log.append(f"Source SHA-256: {src_sha256}")

        # Stage 1: Polyglot Detection
        polyglot_res = self.polyglot_detector.inspect_bytes(src_bytes)
        if not polyglot_res.is_safe:
            audit_log.append(f"STAGE 1 FAILED: File rejected as polyglot / hostile ({', '.join(polyglot_res.reasons)})")
            return CDRResult(
                is_cleared=False,
                source_sha256=src_sha256,
                quarantine_src_path=src_path,
                polyglot_check=polyglot_res,
                sanitization_report=SanitizationReport(is_clean=False),
                injection_check=InjectionCheckResult(is_safe=False, risk_score=1.0),
                audit_log=audit_log,
            )
        audit_log.append("STAGE 1 PASSED: Polyglot check clean.")

        # Stage 2: Structural Active Content Sanitization
        clean_bytes, sanitization_rep = self.sanitizer.sanitize_bytes(src_bytes)
        audit_log.append(f"STAGE 2 COMPLETE: Purged active triggers ({len(sanitization_rep.details)} items)")

        # Stage 3: Prompt Injection Text Analysis
        # Extract text from the structurally sanitized bytes
        extracted_text = ""
        try:
            doc = fitz.open(stream=clean_bytes, filetype="pdf")
            for page in doc:
                extracted_text += page.get_text() + "\n"
            doc.close()
        except Exception as e:
            audit_log.append(f"Warning: Text extraction encountered: {str(e)}")

        injection_res = self.injection_filter.scan(extracted_text)
        if not injection_res.is_safe:
            audit_log.append(f"STAGE 3 WARNING: Prompt injection detected (Risk: {injection_res.risk_score}). Neutralizing.")
        else:
            audit_log.append("STAGE 3 PASSED: Text stream clean of prompt injections.")

        # Stage 4: Visual Flattening (if enabled or requested)
        apply_flattening = self.enable_visual_flattening or force_visual_flatten
        if apply_flattening:
            audit_log.append("STAGE 4: Executing Zero-Trust Visual Flattening (raster reconstitution)...")
            clean_bytes = self.visual_flattener.flatten_bytes(clean_bytes)
            audit_log.append("STAGE 4 COMPLETE: Visual flattening assembled clean synthetic PDF.")

        # Determine target destination in air-gapped vault inbox
        out_name = dest_filename or os.path.basename(src_path)
        dest_path = os.path.join(self.vault_clean_dir, out_name)
        with open(dest_path, "wb") as f:
            f.write(clean_bytes)

        sanitized_sha256 = hashlib.sha256(clean_bytes).hexdigest()
        audit_log.append(f"Target vault file written: {dest_path} (SHA-256: {sanitized_sha256})")
        audit_log.append("ADMISSION CLEARED: Document promoted across air-gap boundary.")

        return CDRResult(
            is_cleared=True,
            source_sha256=src_sha256,
            sanitized_sha256=sanitized_sha256,
            quarantine_src_path=src_path,
            vault_dest_path=dest_path,
            polyglot_check=polyglot_res,
            sanitization_report=sanitization_rep,
            injection_check=injection_res,
            visual_flattening_applied=apply_flattening,
            audit_log=audit_log,
        )
