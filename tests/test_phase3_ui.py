"""Unit & Integration Tests for Phase 3: Three-Plane Workspace UI & Explainer Canvas."""

import unittest
import plotly.graph_objects as go

from privearch.schemas import CalculationVerification, VerificationStatus
from privearch.ui.canvas_protocol import CanvasPayload, CanvasViewType, DerivationStep
from privearch.ui.canvas_generator import CanvasGenerator
try:
    from privearch.ui.three_plane_app import build_three_plane_app
    HAS_GRADIO = True
except ImportError:
    HAS_GRADIO = False
from privearch.os_engine import PrivearchKernel


class TestPhase3UI(unittest.TestCase):
    """Test suite verifying Phase 3 Three-Plane UI and Explainer Canvas deliverables."""

    def test_canvas_protocol_schemas(self):
        """Test Canvas protocol message schemas."""
        step = DerivationStep(
            step_number=1,
            title="Boundary Conditions",
            latex="P = 101325",
            explanation="Given atmospheric pressure"
        )
        self.assertEqual(step.step_number, 1)

        payload = CanvasPayload(
            active_view=CanvasViewType.PLOT_2D,
            title="Thermodynamics",
            derivation_steps=[step]
        )
        self.assertEqual(payload.active_view, CanvasViewType.PLOT_2D)
        self.assertEqual(len(payload.derivation_steps), 1)

    def test_canvas_scientific_plot(self):
        """Test Plotly interactive scientific curve generation."""
        fig = CanvasGenerator.generate_scientific_plot(
            equation_str="P*V = n*R*T",
            target_var="V",
            variables={"P": 101325.0, "T": 300.0, "n": 2.0},
            computed_val=0.04923
        )
        self.assertIsInstance(fig, go.Figure)
        self.assertTrue(len(fig.data) >= 3, "Expected multiple isotherms and operating point")

    def test_canvas_derivation_markdown(self):
        """Test KaTeX derivation breakdown generation."""
        calc = CalculationVerification(
            equation_latex="P*V = n*R*T",
            target_variable="V",
            variables={"P": 101325.0, "T": 300.0, "n": 2.0},
            deterministic_computed_value="0.049234",
            model_predicted_value="0.04923",
            is_verified=True,
            verification_status=VerificationStatus.VERIFIED,
            verification_details="Model matched calculated SymPy ground truth."
        )
        md = CanvasGenerator.generate_derivation_markdown(calc)
        self.assertIn("Symbolic & Numerical Mathematical Derivation", md)
        self.assertIn("P*V = n*R*T", md)
        self.assertIn("0.049234", md)
        self.assertIn("VERIFIED", md)

    def test_canvas_particle_simulation_html(self):
        html = CanvasGenerator.generate_particle_simulation_html(temperature=350.0, pressure=1.5)
        self.assertIn("particleCanvas", html)
        self.assertIn("<iframe", html)
        self.assertIn("temperature", html.lower())
        self.assertIn("requestanimationframe", html.lower())

    def test_canvas_visual_evidence_markdown(self):
        """Test Vision RAG markdown generation for Explainer Canvas."""
        from privearch.schemas import DocumentChunk, ScoredChunk
        chunk = DocumentChunk(
            chunk_id="test_eq1",
            doc_name="test.pdf",
            page_num=10,
            section_header="Bohr Equation",
            text="$$mvr = \\frac{nh}{2\\pi}$$",
            evidence_type="MATHEMATICAL_FORMULA"
        )
        sc = ScoredChunk(chunk=chunk, rrf_score=0.03, final_rank=1)
        md = CanvasGenerator.generate_visual_evidence_markdown([sc])
        self.assertIn("Vision RAG: Formulas, Tables & Visual Evidence", md)
        self.assertIn("Extracted LaTeX Formula", md)
        self.assertIn("test.pdf", md)

    @unittest.skip("Legacy Gradio frontend deprecated in favor of native WinUI 3 desktop workstation")
    def test_build_three_plane_app(self):
        """Test building the complete Three-Plane Workspace UI."""
        kernel = PrivearchKernel()
        app = build_three_plane_app(kernel=kernel)
        self.assertIsNotNone(app)
        self.assertEqual(app.title, "Privreach OS - Multimodal Research Workstation")


if __name__ == "__main__":
    unittest.main()

