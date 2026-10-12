"""
Polyglot Payload and Multi-Format Collision Detector.

Identifies and rejects files that simultaneously masquerade as valid PDFs
while embedding secondary executable or archive payloads (e.g. ZIP, HTML, JAR, PE/EXE).
"""

from typing import List, Dict, Tuple, Optional
from pydantic import BaseModel, Field


class PolyglotCheckResult(BaseModel):
    is_safe: bool
    is_polyglot: bool
    detected_formats: List[str] = Field(default_factory=list)
    risk_level: str = "LOW"  # LOW, MEDIUM, CRITICAL
    reasons: List[str] = Field(default_factory=list)


MAGIC_SIGNATURES: List[Tuple[bytes, str, int]] = [
    # (magic_bytes, format_name, max_offset)
    (b"%PDF", "PDF", 1024),
    (b"PK\x03\x04", "ZIP_ARCHIVE", -1),
    (b"PK\x05\x06", "ZIP_END_OF_CENTRAL_DIR", -1),
    (b"MZ", "DOS_PE_EXECUTABLE", 16),
    (b"\x7fELF", "LINUX_ELF_BINARY", 16),
    (b"<html", "HTML_DOCUMENT", 2048),
    (b"<!DOCTYPE html", "HTML_DOCUMENT", 2048),
    (b"<script", "JAVASCRIPT_DOCUMENT", -1),
    (b"Rar!\x1a\x07", "RAR_ARCHIVE", 64),
    (b"7z\xbc\xaf\x27\x1c", "7ZIP_ARCHIVE", 64),
    (b"\x1f\x8b\x08", "GZIP_STREAM", 64),
]


class PolyglotDetector:
    """
    Zero-trust pre-flight validator for incoming document streams.
    """

    def __init__(self, max_prefix_bytes: int = 4096):
        self.max_prefix_bytes = max_prefix_bytes

    def inspect_bytes(self, data: bytes) -> PolyglotCheckResult:
        """
        Inspects binary buffer for multi-format collisions and malformed headers.
        """
        if not data:
            return PolyglotCheckResult(
                is_safe=False,
                is_polyglot=False,
                detected_formats=[],
                risk_level="CRITICAL",
                reasons=["Empty byte payload"],
            )

        # 1. Must have valid PDF header in the opening segment
        header_segment = data[: self.max_prefix_bytes]
        pdf_index = header_segment.find(b"%PDF")
        if pdf_index == -1:
            return PolyglotCheckResult(
                is_safe=False,
                is_polyglot=False,
                detected_formats=["UNKNOWN"],
                risk_level="CRITICAL",
                reasons=["Missing mandatory '%PDF' magic header"],
            )

        detected_formats = ["PDF"]
        reasons: List[str] = []

        # 2. Check for conflicting binary format signatures
        for sig, fmt, max_offset in MAGIC_SIGNATURES:
            if fmt == "PDF":
                continue

            if max_offset == -1:
                # Search entire file or first 1MB
                search_window = data[: 1024 * 1024]
                if sig.lower() in search_window.lower():
                    detected_formats.append(fmt)
                    reasons.append(f"Found embedded signature for {fmt}")
            else:
                if sig in data[:max_offset]:
                    detected_formats.append(fmt)
                    reasons.append(f"Header contains prefix collision with {fmt}")

        # 3. Check for suspicious prepended padding before %PDF
        if pdf_index > 0:
            pre_pdf_bytes = data[:pdf_index]
            # If not just comments or whitespace, it's suspect
            if any(b not in b"\r\n\t " and (b < 32 or b > 126) for b in pre_pdf_bytes):
                reasons.append(f"Suspicious binary preamble of {pdf_index} bytes prior to %PDF")

        # 4. Determine safety and risk level
        is_polyglot = len(set(detected_formats)) > 1
        is_safe = (not is_polyglot) and (len(reasons) == 0)

        risk_level = "LOW"
        if is_polyglot:
            risk_level = "CRITICAL"
        elif reasons:
            risk_level = "MEDIUM"

        return PolyglotCheckResult(
            is_safe=is_safe,
            is_polyglot=is_polyglot,
            detected_formats=detected_formats,
            risk_level=risk_level,
            reasons=reasons,
        )

    def inspect_file(self, file_path: str) -> PolyglotCheckResult:
        """Inspects file from disk."""
        try:
            with open(file_path, "rb") as f:
                data = f.read()
            return self.inspect_bytes(data)
        except Exception as e:
            return PolyglotCheckResult(
                is_safe=False,
                is_polyglot=False,
                detected_formats=[],
                risk_level="CRITICAL",
                reasons=[f"File read error: {str(e)}"],
            )
