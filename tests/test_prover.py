"""
Unit and Integration Tests for privreach.prover zero-hallucination engine.
"""

import unittest
from privreach.schemas import DocumentChunk
from privreach.prover.claim_decomposer import ClaimDecomposer
from privreach.prover.span_matcher import SpanMatcher
from privreach.prover.grounding_gate import GroundingGate
from privreach.prover.confidence_report import VerificationVerdict


class TestProverSubsystem(unittest.TestCase):
    """Verifies zero-hallucination proof and span attribution engine."""

    def setUp(self):
        self.decomposer = ClaimDecomposer()
        self.matcher = SpanMatcher()
        self.gate_strict = GroundingGate(strict_mode=True)
        self.gate_lenient = GroundingGate(strict_mode=False)

        # Simulated evidence from peer-reviewed paper in the vault
        self.chunks = [
            DocumentChunk(
                chunk_id="c_litho_001",
                doc_name="asml_high_na_euv_2024.pdf",
                page_num=4,
                section_header="Optical Specifications",
                text=(
                    "The High-NA EUV lithography tool employs an anamorphic optical design "
                    "with a numerical aperture of 0.55. It operates at an extreme ultraviolet "
                    "wavelength of 13.5 nanometers using a laser-produced tin plasma source. "
                    "The magnification is 4x in the x-direction and 8x in the y-direction."
                ),
                char_count=298,
                word_count=45,
                evidence_type="text",
            ),
            DocumentChunk(
                chunk_id="c_litho_002",
                doc_name="asml_high_na_euv_2024.pdf",
                page_num=5,
                section_header="Stochastic Defectivity",
                text=(
                    "Stochastic defects during EUV exposure are mitigated through optimized "
                    "chemically amplified resists and carbon-nanotube pellicles capable of "
                    "withstanding 400 watts of source power."
                ),
                char_count=230,
                word_count=28,
                evidence_type="text",
            ),
        ]

    def test_claim_decomposer(self):
        """Splits multi-sentence synthesis text into discrete atomic claims."""
        text = (
            "Overall, the tool operates at 13.5nm wavelength. "
            "Furthermore, it uses a laser-produced tin plasma source. "
            "In conclusion, the system is highly effective."
        )
        claims = self.decomposer.decompose(text)
        self.assertGreaterEqual(len(claims), 2)
        # Verify discourse filler is stripped in normalized representation
        first_claim = claims[0].normalized_text
        self.assertFalse(first_claim.lower().startswith("overall,"))

    def test_exact_span_matching(self):
        """Matches verbatim claim directly back to source document chunk."""
        claim = "The High-NA EUV lithography tool employs an anamorphic optical design with a numerical aperture of 0.55."
        res = self.matcher.match_claim(claim, self.chunks)

        self.assertTrue(res.is_matched)
        self.assertEqual(res.match_type, "exact")
        self.assertEqual(res.source_doc, "asml_high_na_euv_2024.pdf")
        self.assertEqual(res.source_page, 4)
        self.assertEqual(res.source_chunk_id, "c_litho_001")

    def test_fuzzy_token_span_matching(self):
        """Slight rephrasing should still match with fuzzy token attribution."""
        rephrased_claim = "High-NA EUV uses a numerical aperture of 0.55 with an anamorphic optical design."
        res = self.matcher.match_claim(rephrased_claim, self.chunks)

        self.assertTrue(res.is_matched)
        self.assertIn(res.match_type, ["exact", "fuzzy"])
        self.assertEqual(res.source_doc, "asml_high_na_euv_2024.pdf")

    def test_unsupported_hallucination_detected(self):
        """Complete hallucination with zero evidence in vault must fail matching."""
        hallucinated_claim = "The system incorporates a nuclear-powered fusion laser operating at 2.4 gigawatts."
        res = self.matcher.match_claim(hallucinated_claim, self.chunks)

        self.assertFalse(res.is_matched)
        self.assertEqual(res.match_type, "none")
        self.assertLess(res.similarity_score, 0.40)

    def test_strict_grounding_gate_strips_hallucinations(self):
        """In strict mode, unsupported hallucinated sentences must be eliminated from output."""
        llm_synthesis = (
            "The High-NA EUV tool employs an anamorphic optical design with a numerical aperture of 0.55. "
            "The system incorporates a nuclear-powered fusion laser operating at 2.4 gigawatts. "
            "It operates at an extreme ultraviolet wavelength of 13.5 nanometers using a laser-produced tin plasma source."
        )

        report = self.gate_strict.verify_and_gate(llm_synthesis, self.chunks)

        self.assertEqual(report.total_claims, 3)
        self.assertEqual(report.verified_claims, 2)
        self.assertEqual(report.unsupported_claims, 1)
        self.assertAlmostEqual(report.grounding_ratio, 2 / 3, places=2)
        self.assertFalse(report.is_strictly_verified)

        # The hallucination must be completely stripped from verified_text
        self.assertNotIn("nuclear-powered fusion laser", report.verified_text)
        # The verified claims must be present
        self.assertIn("0.55", report.verified_text)
        self.assertIn("13.5 nanometers", report.verified_text)

    def test_lenient_grounding_gate_flags_hallucinations(self):
        """In lenient mode, unsupported sentences are flagged with [UNSUPPORTED CLAIM]."""
        llm_synthesis = "The system incorporates a nuclear-powered fusion laser operating at 2.4 gigawatts."
        report = self.gate_lenient.verify_and_gate(llm_synthesis, self.chunks)

        self.assertIn("[UNSUPPORTED CLAIM]", report.verified_text)


if __name__ == "__main__":
    unittest.main()
