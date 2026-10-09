"""Vision RAG & Advanced Document Understanding for Scientific Literature.

Features:
1. 2D Spatial Layout Math Formula Reconstruction (Converting fractions & symbols to LaTeX)
2. Structural Table Extraction (Converting PDF tables into Clean Markdown)
3. Visual Figure & Diagram Extraction (Extracting high-res apparatus schemes, charts & orbits)
4. Surrounding Context Fusion (Linking captions, variable definitions, and units)
"""

import os
import re
import sys
from typing import Dict, List, Any, Optional, Tuple
import pymupdf
from PIL import Image

from privearch.schemas import DocumentChunk


# Standard Greek and scientific symbol mappings from Symbol / Math fonts
SYMBOL_MAP = {
    '': r'\alpha',
    '': r'\beta',
    '': r'\gamma',
    '': r'\delta',
    '': r'\epsilon',
    '': r'\theta',
    '': r'\lambda',
    '': r'\mu',
    '': r'\nu',
    '': r'\pi',
    '': r'\rho',
    '': r'\sigma',
    '': r'\tau',
    '': r'\omega',
    '': r'\Delta',
    '': r'\Omega',
    '': r'\Sigma',
    '': r'^\oplus',
    '⊝': r'^\ominus',
    '−': '-',
    '⎯→': r'\rightarrow',
    '→': r'\rightarrow',
    '⇌': r'\rightleftharpoons',
    '×': r'\times',
    '±': r'\pm',
    '≤': r'\le',
    '≥': r'\ge',
    '≠': r'\ne',
    '≈': r'\approx',
    '': r'\infty',
    '': r'\propto',
    'ħ': r'\hbar',
    'Å': r'\text{\AA}'
}


def sanitize_math_symbols(text: str) -> str:
    """Replace font-encoded math glyphs with standard LaTeX equivalents."""
    for char, rep in SYMBOL_MAP.items():
        text = text.replace(char, rep)
    return text


class VisionDocumentExtractor:
    """
    Advanced Document Understanding Engine:
    Parses complex scientific PDFs extracting LaTeX formulas, structured Markdown tables,
    and high-resolution visual diagrams.
    """

    def __init__(self, artifacts_dir: str = ".privearch_artifacts"):
        self.artifacts_dir = os.path.abspath(artifacts_dir)
        self.figures_dir = os.path.join(self.artifacts_dir, "figures")
        os.makedirs(self.figures_dir, exist_ok=True)

    def extract_tables_from_page(self, page: pymupdf.Page, page_num: int, doc_name: str) -> List[DocumentChunk]:
        """Extract structured tables and serialize to Markdown chunks."""
        table_chunks: List[DocumentChunk] = []
        try:
            tabs = page.find_tables()
            for idx, tab in enumerate(tabs):
                df_rows = tab.extract()
                if not df_rows or len(df_rows) < 2:
                    continue

                # Clean cell values
                clean_matrix = []
                for row in df_rows:
                    clean_row = [str(c or "").replace("\n", " ").strip() for c in row]
                    if any(clean_row):
                        clean_matrix.append(clean_row)

                if len(clean_matrix) < 2:
                    continue

                header = clean_matrix[0]
                num_cols = len(header)
                separator = ["---"] * num_cols

                md_lines = [
                    f"### 📊 Structured Table (Page {page_num})",
                    "| " + " | ".join(header) + " |",
                    "| " + " | ".join(separator) + " |"
                ]

                for row in clean_matrix[1:]:
                    padded_row = row + [""] * (num_cols - len(row))
                    md_lines.append("| " + " | ".join(padded_row[:num_cols]) + " |")

                table_md = "\n".join(md_lines)
                table_chunks.append(DocumentChunk(
                    chunk_id=f"{doc_name}_p{page_num}_tbl{idx+1}",
                    doc_name=doc_name,
                    page_num=page_num,
                    section_header=f"Scientific Table (Page {page_num})",
                    text=table_md,
                    char_count=len(table_md),
                    word_count=len(table_md.split()),
                    evidence_type="STRUCTURED_TABLE"
                ))
        except Exception:
            pass

        return table_chunks

    def extract_figures_from_page(self, doc: pymupdf.Document, page: pymupdf.Page, page_num: int, doc_name: str) -> List[DocumentChunk]:
        """Extract scientific figures, charts, and apparatus diagrams as visual evidence chunks."""
        figure_chunks: List[DocumentChunk] = []
        try:
            image_infos = page.get_image_info(xrefs=True)
            for idx, info in enumerate(image_infos):
                w = info.get("width", 0)
                h = info.get("height", 0)
                xref = info.get("xref", 0)

                # Filter out tiny icon glyphs or full-page background stamps
                if (w >= 120 and h >= 70) and not (w > 1200 and h > 1600):
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image.get("image")
                    ext = base_image.get("ext", "png")

                    if not image_bytes:
                        continue

                    fig_filename = f"{os.path.splitext(doc_name)[0]}_p{page_num}_fig{idx+1}.{ext}"
                    fig_path = os.path.join(self.figures_dir, fig_filename)

                    with open(fig_path, "wb") as f_out:
                        f_out.write(image_bytes)

                    # Inspect surrounding page text for figure caption
                    bbox = info.get("bbox", (0, 0, 0, 0))
                    caption = self._find_nearby_caption(page, bbox)

                    fig_desc = (
                        f"### 🔬 Scientific Figure & Diagram: {caption or f'Figure on Page {page_num}'}\n"
                        f"**Source Document:** `{doc_name}` (Page {page_num})  \n"
                        f"**Resolution:** {w} × {h} px  \n"
                        f"**Visual Artifact Path:** `{fig_path}`\n\n"
                        f"*Context:* {caption if caption else 'Scientific experimental apparatus or molecular diagram.'}"
                    )

                    figure_chunks.append(DocumentChunk(
                        chunk_id=f"{doc_name}_p{page_num}_fig{idx+1}",
                        doc_name=doc_name,
                        page_num=page_num,
                        section_header=f"Figure: {caption[:40]}" if caption else f"Figure (Page {page_num})",
                        text=fig_desc,
                        char_count=len(fig_desc),
                        word_count=len(fig_desc.split()),
                        evidence_type="VISUAL_FIGURE",
                        media_path=fig_path
                    ))
        except Exception:
            pass

        return figure_chunks

    def _find_nearby_caption(self, page: pymupdf.Page, img_bbox: Tuple[float, float, float, float]) -> str:
        """Find text blocks directly above or below the image bounding box that look like captions."""
        y0, y1 = img_bbox[1], img_bbox[3]
        blocks = page.get_text("blocks")
        candidate_captions = []

        for b in blocks:
            b_y0, b_y1 = b[1], b[3]
            txt = b[4].strip()
            # If block is within 60 points below or above the image
            if (abs(b_y0 - y1) < 65 or abs(y0 - b_y1) < 45) and len(txt) > 5:
                if any(k in txt.lower() for k in ["fig", "figure", "scheme", "diagram", "bohr", "apparatus", "model", "orbit"]):
                    return txt.replace("\n", " ").strip()
                candidate_captions.append(txt.replace("\n", " ").strip())

        return candidate_captions[0] if candidate_captions else ""

    def reconstruct_spatial_formulas(self, page: pymupdf.Page, page_num: int, doc_name: str) -> List[DocumentChunk]:
        """
        Detects 2D spatial arrangements (numerators, fraction bars, denominators, subscripts)
        and reconstructs them into rigorous LaTeX equations.
        """
        formula_chunks: List[DocumentChunk] = []
        words = page.get_text("words")
        if not words:
            return formula_chunks

        # Sort words primarily by vertical y0, then horizontal x0
        words_sorted = sorted(words, key=lambda w: (round(w[1] / 6.0) * 6.0, w[0]))

        # Heuristic 1: Detect explicit equals signs and cluster surrounding terms within horizontal window
        eq_tokens = [w for w in words if w[4] in ("=", "==") or "=" in w[4]]
        processed_y_centers = []

        for eq in eq_tokens:
            eq_x, eq_y = eq[0], eq[1]
            if any(abs(eq_y - py) < 18 for py in processed_y_centers):
                continue

            processed_y_centers.append(eq_y)

            # Gather words within vertical band (+/- 26 pt) and horizontal band (+/- 140 pt)
            local_words = [
                w for w in words
                if abs(w[1] - eq_y) <= 26 and abs(w[0] - eq_x) <= 140
            ]

            if len(local_words) < 2:
                continue

            # Classify words into numerator (above eq_y - 4), midline (|y - eq_y| <= 4), and denominator (below eq_y + 4)
            numerators = [w for w in local_words if w[1] < eq_y - 4.0]
            midlines = [w for w in local_words if abs(w[1] - eq_y) <= 4.0]
            denominators = [w for w in local_words if w[1] > eq_y + 4.0]

            num_str = " ".join(sanitize_math_symbols(w[4]) for w in sorted(numerators, key=lambda w: w[0])).strip()
            mid_str = " ".join(sanitize_math_symbols(w[4]) for w in sorted(midlines, key=lambda w: w[0])).strip()
            den_str = " ".join(sanitize_math_symbols(w[4]) for w in sorted(denominators, key=lambda w: w[0])).strip()

            reconstructed_latex = ""
            if num_str and den_str:
                # We have a vertical fraction!
                reconstructed_latex = f"{mid_str} \\frac{{{num_str}}}{{{den_str}}}"
            elif mid_str:
                reconstructed_latex = mid_str

            reconstructed_latex = self._clean_latex_syntax(reconstructed_latex)

            if len(reconstructed_latex) >= 4 and "=" in reconstructed_latex:
                desc = (
                    f"### 📐 Mathematical Formula (Page {page_num})\n"
                    f"**Governing Equation:** $${reconstructed_latex}$$\n\n"
                    f"*Extracted from scientific literature page {page_num}.*"
                )
                formula_chunks.append(DocumentChunk(
                    chunk_id=f"{doc_name}_p{page_num}_eq{len(formula_chunks)+1}",
                    doc_name=doc_name,
                    page_num=page_num,
                    section_header=f"Formula (Page {page_num})",
                    text=desc,
                    char_count=len(desc),
                    word_count=len(desc.split()),
                    evidence_type="MATHEMATICAL_FORMULA"
                ))

        return formula_chunks

    def _clean_latex_syntax(self, raw: str) -> str:
        """Standardizes LaTeX syntax into clean display formulations."""
        s = raw
        # Clean double equals or fragmented tokens
        s = re.sub(r'=\s*=', '=', s)
        s = s.replace("", r"\nu").replace("", r"\Delta")
        s = s.replace("", r"\pi").replace("ħ", r"\hbar")
        s = re.sub(r'\bm\s+vr\b', 'm v r', s)
        s = re.sub(r'\bmvr\b', 'm v r', s)
        s = re.sub(r'\bnh\s+2\s*\\pi\b', r'\\frac{nh}{2\\pi}', s)
        return s.strip()

    def extract_document(self, pdf_path: str, extract_figures: bool = True) -> Dict[str, Any]:
        """
        Complete Multi-Modal & Structural Document Extraction:
        Extracts clean text, structured tables, visual figures, and reconstructed mathematical formulas.
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        doc = pymupdf.open(pdf_path)
        doc_name = os.path.basename(pdf_path)
        file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)

        pages_data = []
        all_special_chunks: List[DocumentChunk] = []

        current_section = "General Scientific Literature"

        for page_idx in range(len(doc)):
            page = doc[page_idx]
            page_num = page_idx + 1

            # 1. Infer section header
            blocks = page.get_text("blocks")
            detected_header = current_section
            for b in blocks:
                txt = b[4].strip()
                if txt and len(txt.split()) <= 8 and (
                    txt.isupper() or re.match(r'^(Unit|Chapter|Section|\d+\.|\d+\.\d+)', txt, re.IGNORECASE)
                ):
                    detected_header = txt.replace("\n", " ")
                    current_section = detected_header
                    break

            # 2. Extract Tables
            table_chunks = self.extract_tables_from_page(page, page_num, doc_name)
            all_special_chunks.extend(table_chunks)

            # 3. Extract Figures
            if extract_figures:
                fig_chunks = self.extract_figures_from_page(doc, page, page_num, doc_name)
                all_special_chunks.extend(fig_chunks)

            # 4. Reconstruct 2D Math Formulas
            formula_chunks = self.reconstruct_spatial_formulas(page, page_num, doc_name)
            all_special_chunks.extend(formula_chunks)

            # 5. Extract Prose Text
            raw_text = page.get_text("text")
            cleaned_text = sanitize_math_symbols(raw_text)

            pages_data.append({
                "page_num": page_num,
                "text": cleaned_text,
                "section_header": detected_header
            })

        total_pages = len(doc)
        doc.close()

        return {
            "doc_name": doc_name,
            "file_path": os.path.abspath(pdf_path),
            "page_count": total_pages,
            "file_size_mb": round(file_size_mb, 2),
            "pages": pages_data,
            "special_chunks": all_special_chunks
        }
