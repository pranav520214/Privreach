"""Unit & Integration Tests for Vision RAG & Formula Extraction Engine."""

import os
import unittest
import pymupdf

from privearch.ingestion.vision_extractor import (
    VisionDocumentExtractor,
    sanitize_math_symbols,
    SYMBOL_MAP
)
from privearch.schemas import DocumentChunk, ScoredChunk
from privearch.ui.canvas_generator import CanvasGenerator


class TestVisionRAG(unittest.TestCase):
    """Test suite verifying 2D math reconstruction, tables, and visual diagram extraction."""

    def setUp(self):
        self.extractor = VisionDocumentExtractor(artifacts_dir=".privearch_test_artifacts")

    def tearDown(self):
        # Clean up test artifacts directory if created
        if os.path.exists(".privearch_test_artifacts"):
            import shutil
            shutil.rmtree(".privearch_test_artifacts", ignore_errors=True)

    def test_sanitize_math_symbols(self):
        """Test conversion of font-encoded symbols to LaTeX equivalents."""
        raw = "Energy difference E = h and angular momentum mvr = nh / 2"
        sanitized = sanitize_math_symbols(raw)
        self.assertIn(r"\Delta", sanitized)
        self.assertIn(r"\nu", sanitized)
        self.assertIn(r"\pi", sanitized)

    def test_clean_latex_syntax(self):
        """Test formula cleanup and standardization."""
        raw_eq = "mvr == nh 2\\pi"
        cleaned = self.extractor._clean_latex_syntax(raw_eq)
        self.assertEqual(cleaned, r"m v r = \frac{nh}{2\pi}")

    def test_visual_evidence_markdown_generation(self):
        """Test formatting of extracted figures and tables for the Explainer Canvas."""
        formula_chunk = DocumentChunk(
            chunk_id="test_eq1",
            doc_name="Bohr_Model.pdf",
            page_num=5,
            section_header="Bohr Quantization Rule",
            text="$$m v r = \\frac{n h}{2 \\pi}$$",
            evidence_type="MATHEMATICAL_FORMULA"
        )
        figure_chunk = DocumentChunk(
            chunk_id="test_fig1",
            doc_name="Bohr_Model.pdf",
            page_num=6,
            section_header="Bohr Orbit Scheme",
            text="### Diagram of stationary energy levels",
            evidence_type="VISUAL_FIGURE",
            media_path=".privearch_artifacts/figures/test_orbit.png"
        )
        table_chunk = DocumentChunk(
            chunk_id="test_tbl1",
            doc_name="Bohr_Model.pdf",
            page_num=7,
            section_header="Energy Levels Table",
            text="| n | E_n (eV) |\n|---|---|\n| 1 | -13.6 |",
            evidence_type="STRUCTURED_TABLE"
        )

        scored = [
            ScoredChunk(chunk=formula_chunk, rrf_score=0.033, final_rank=1),
            ScoredChunk(chunk=figure_chunk, rrf_score=0.031, final_rank=2),
            ScoredChunk(chunk=table_chunk, rrf_score=0.029, final_rank=3)
        ]

        md = CanvasGenerator.generate_visual_evidence_markdown(scored)
        self.assertIn("Vision RAG: Formulas, Tables & Visual Evidence", md)
        self.assertIn("Extracted LaTeX Formula", md)
        self.assertIn("Visual Figure: Bohr Orbit Scheme", md)
        self.assertIn("Structured Data Table", md)
        self.assertIn("-13.6", md)


if __name__ == "__main__":
    unittest.main()
