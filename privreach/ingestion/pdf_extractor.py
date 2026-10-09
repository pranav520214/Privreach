"""High-speed local PDF extractor using PyMuPDF."""

import os
import re
from typing import Dict, List, Any
import pymupdf


def clean_scientific_text(text: str) -> str:
    """Normalize text while preserving scientific notation, formulas, and symbols."""
    if not text:
        return ""
    # Normalize unicode hyphens and dashes
    text = text.replace("\u2010", "-").replace("\u2013", "-").replace("\u2014", "-")
    # Fix broken hyphenated words across line breaks (e.g. con-\ncentration -> concentration)
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
    # Replace non-breaking spaces and soft hyphens
    text = text.replace('\xa0', ' ').replace('\xad', '')
    # Replace excess whitespace while preserving paragraph breaks
    lines = [line.strip() for line in text.splitlines()]
    reconstructed = []
    for line in lines:
        if not line:
            if reconstructed and reconstructed[-1] != "":
                reconstructed.append("")
        else:
            if reconstructed and reconstructed[-1] != "" and not reconstructed[-1].endswith(('.', ':', ';', '?', '!')):
                # Append to current paragraph
                reconstructed[-1] += " " + line
            else:
                reconstructed.append(line)
    return "\n\n".join(reconstructed).strip()


def extract_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Extracts text, page mappings, and structural markers from a PDF file.
    
    Returns:
        Dict containing doc_name, page_count, file_size_mb, and pages list.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")

    doc = pymupdf.open(pdf_path)
    file_name = os.path.basename(pdf_path)
    file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)

    pages = []
    current_section = "General Introduction"

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        raw_text = page.get_text("text")

        # Try to infer section header from first text block or prominent lines
        blocks = page.get_text("blocks")
        detected_header = current_section
        if blocks:
            for b in blocks:
                block_text = b[4].strip()
                if block_text and len(block_text.split()) <= 8 and (
                    block_text.isupper() or
                    re.match(r'^(Unit|Chapter|Section|\d+\.|\d+\.\d+)', block_text, re.IGNORECASE)
                ):
                    detected_header = block_text.replace('\n', ' ')
                    current_section = detected_header
                    break

        cleaned = clean_scientific_text(raw_text)
        if cleaned:
            pages.append({
                "page_num": page_idx + 1,
                "text": cleaned,
                "section_header": detected_header
            })

    total_pages = len(doc)
    doc.close()

    return {
        "doc_name": file_name,
        "file_path": os.path.abspath(pdf_path),
        "page_count": total_pages,
        "file_size_mb": round(file_size_mb, 2),
        "pages": pages
    }
