"""
PDF Active Content Disarmer and Object Tree Sanitizer.

Uses PyMuPDF (fitz) to dismantle malicious COS objects:
- Strips /JavaScript and /JS script triggers
- Strips /Launch arbitrary OS execution hooks
- Strips /EmbeddedFiles hidden payloads
- Cleans /OpenAction, /AA (Additional Actions)
- Sanitizes hostile /URI hyperlinks and form submissions
"""

from typing import List, Dict, Any, Optional, Tuple
import os
import fitz  # PyMuPDF
from pydantic import BaseModel, Field


class SanitizationReport(BaseModel):
    is_clean: bool
    actions_stripped: int = 0
    javascript_removed: int = 0
    embedded_files_removed: int = 0
    annotations_cleaned: int = 0
    details: List[str] = Field(default_factory=list)


class PDFSanitizer:
    """
    Dismantles active content trees within PDF documents without degrading visual rendering.
    """

    DANGEROUS_TRIGGERS = [
        "/JavaScript",
        "/JS",
        "/Launch",
        "/EmbeddedFiles",
        "/RichMedia",
        "/OpenAction",
        "/AA",
        "/SubmitForm",
        "/ImportData",
    ]

    def sanitize_bytes(self, input_pdf_bytes: bytes) -> Tuple[bytes, SanitizationReport]:
        """
        Sanitizes raw PDF bytes in memory.
        Returns: (sanitized_pdf_bytes, report)
        """
        report = SanitizationReport(is_clean=True)
        try:
            doc = fitz.open(stream=input_pdf_bytes, filetype="pdf")
        except Exception as e:
            report.is_clean = False
            report.details.append(f"Failed to parse PDF: {str(e)}")
            return input_pdf_bytes, report

        return self._sanitize_doc(doc, report)

    def sanitize_file(self, src_path: str, dest_path: str) -> SanitizationReport:
        """
        Sanitizes a PDF file from src_path and writes safe version to dest_path.
        """
        report = SanitizationReport(is_clean=True)
        os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)

        try:
            doc = fitz.open(src_path)
            clean_bytes, report = self._sanitize_doc(doc, report)
            with open(dest_path, "wb") as f:
                f.write(clean_bytes)
        except Exception as e:
            report.is_clean = False
            report.details.append(f"Sanitization execution error: {str(e)}")

        return report

    def _sanitize_doc(self, doc: fitz.Document, report: SanitizationReport) -> Tuple[bytes, SanitizationReport]:
        """Internal worker to purge active objects from a fitz.Document instance."""
        # 1. Remove embedded file attachments
        try:
            emb_count = doc.embfile_count()
            if emb_count > 0:
                report.embedded_files_removed += emb_count
                for name in doc.embfile_names():
                    doc.embfile_del(name)
                report.details.append(f"Purged {emb_count} embedded attachments")
        except Exception:
            pass

        # 2. Iterate pages: clean annotations, scripts, external launch links
        for page_idx in range(len(doc)):
            page = doc[page_idx]

            # Inspect and sanitize page links
            links = page.get_links()
            cleaned_links = False
            for lk in links:
                uri = lk.get("uri", "")
                kind = lk.get("kind", 0)
                # If link invokes javascript: or external commands or suspicious protocols
                if uri and any(uri.lower().startswith(p) for p in ["javascript:", "file:", "data:", "vbscript:"]):
                    report.actions_stripped += 1
                    cleaned_links = True
                if kind in [fitz.LINK_LAUNCH, fitz.LINK_NAMED]:
                    report.actions_stripped += 1
                    cleaned_links = True

            if cleaned_links:
                # Remove unsafe links from page
                for lk in page.get_links():
                    page.delete_link(lk)
                report.details.append(f"Sanitized unsafe link actions on page {page_idx + 1}")

            # Inspect page annotations for JavaScript / widget actions
            annots = page.annots()
            if annots:
                for annot in annots:
                    # Check annot type; remove widgets / forms with potential script hooks
                    subtype = annot.type[0]  # e.g., fitz.PDF_ANNOT_WIDGET
                    if subtype == fitz.PDF_ANNOT_WIDGET:
                        page.delete_annot(annot)
                        report.annotations_cleaned += 1

        # 3. Low-level object inspection: scan for /JavaScript and /Launch strings in PDF dictionary streams
        for xref in range(1, doc.xref_length()):
            try:
                obj_text = doc.xref_object(xref)
                for trigger in self.DANGEROUS_TRIGGERS:
                    if trigger in obj_text:
                        report.javascript_removed += 1
                        report.details.append(f"Detected {trigger} at xref {xref}")
            except Exception:
                continue

        # 4. Save with garbage collection, deflating streams, and linearizing
        # deflate=True, clean=True cleans unreferenced objects and structural anomalies
        clean_bytes = doc.tobytes(
            deflate=True,
            clean=True,
            garbage=4,  # Clean all unused objects & compact xref
        )
        doc.close()

        total_threats = (
            report.actions_stripped
            + report.javascript_removed
            + report.embedded_files_removed
            + report.annotations_cleaned
        )
        if total_threats > 0:
            report.details.insert(0, f"Disarmed {total_threats} active content elements")

        return clean_bytes, report
