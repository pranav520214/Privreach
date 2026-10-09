"""Unit & Integration Tests for R1 / CoT Reasoning & Deep Thinking Engine."""

import unittest
from privearch.models.reasoning_engine import (
    ReasoningEngine,
    extract_thought_trace,
    is_reasoning_model
)
from privearch.models.synthesis_engine import SynthesisOutput
from privearch.schemas import DocumentChunk, ScoredChunk, ReasoningStage, ReasoningStep
from privearch.ui.canvas_generator import CanvasGenerator


class TestReasoningEngine(unittest.TestCase):
    """Test suite verifying R1 / CoT thought extraction, cognitive decomposition, and synthesis separation."""

    def setUp(self):
        self.engine = ReasoningEngine()

    def test_extract_thought_trace_complete_block(self):
        """Test separating <think>...</think> from clean academic synthesis."""
        raw = (
            "<think>\n"
            "1. First, examine the Bohr angular momentum relation mvr = nh / (2pi).\n"
            "2. Next, cross-check de Broglie relation lambda = h / (mv).\n"
            "3. Notice 2*pi*r = n*lambda corresponds to standing waves.\n"
            "</think>\n\n"
            "### Bohr Orbit Quantization and Matter Waves\n"
            "According to de Broglie's hypothesis [1], electrons exhibit wave-particle duality."
        )
        clean_synth, trace = extract_thought_trace(raw)
        self.assertIsNotNone(trace)
        self.assertIn("Bohr angular momentum relation", trace)
        self.assertNotIn("<think>", clean_synth)
        self.assertNotIn("</think>", clean_synth)
        self.assertIn("### Bohr Orbit Quantization", clean_synth)
        self.assertIn("According to de Broglie's hypothesis [1]", clean_synth)

    def test_extract_thought_trace_unclosed(self):
        """Test graceful recovery when a model leaves <think> unclosed."""
        raw = (
            "<think>\n"
            "Analyzing momentum...\n"
            "### Final Answer\n"
            "The wavelength is given by h/p [1]."
        )
        clean_synth, trace = extract_thought_trace(raw)
        self.assertIsNotNone(trace)
        self.assertIn("Analyzing momentum", trace)
        self.assertIn("### Final Answer", clean_synth)

    def test_extract_thought_trace_prefilled_prompt(self):
        """Test completion where prompt already ended with <think> and model only outputs </think>."""
        raw = (
            "Deliberating on de Broglie standing wave condition 2*pi*r = n*lambda...\n"
            "Checking momentum definitions...\n"
            "</think>\n\n"
            "### Academic Synthesis\n"
            "Matter waves satisfy lambda = h/p [1]."
        )
        clean_synth, trace = extract_thought_trace(raw)
        self.assertIsNotNone(trace)
        self.assertIn("Deliberating on de Broglie", trace)
        self.assertNotIn("</think>", clean_synth)
        self.assertIn("### Academic Synthesis", clean_synth)
        self.assertIn("Matter waves satisfy lambda = h/p [1].", clean_synth)

    def test_extract_thought_trace_multiple_blocks(self):
        """Test extraction when model outputs multiple <think> blocks."""
        raw = (
            "<think>Stage 1 thinking</think>\n"
            "Intermediate notes\n"
            "<think>Stage 2 thinking</think>\n"
            "### Final Answer\n"
            "Clean content [1]."
        )
        clean_synth, trace = extract_thought_trace(raw)
        self.assertIsNotNone(trace)
        self.assertIn("Stage 1 thinking", trace)
        self.assertIn("Stage 2 thinking", trace)
        self.assertNotIn("<think>", clean_synth)
        self.assertNotIn("</think>", clean_synth)
    def test_extract_thought_trace_none(self):
        """Test passthrough when no <think> tags are present."""
        raw = "Direct synthesis without thinking block [1]."
        clean_synth, trace = extract_thought_trace(raw)
        self.assertIsNone(trace)
        self.assertEqual(clean_synth, raw)

    def test_is_reasoning_model(self):
        """Test R1 model identifier detection."""
        self.assertTrue(is_reasoning_model("deepseek-r1:1.5b"))
        self.assertTrue(is_reasoning_model("deepseek-r1:7b"))
        self.assertTrue(is_reasoning_model("DeepSeek-R1-Distill-Qwen-1.5B"))
        self.assertFalse(is_reasoning_model("qwen2.5-coder:3b"))
        self.assertFalse(is_reasoning_model("medgemma:4b"))

    def test_decompose_reasoning_steps(self):
        """Test 5-stage cognitive decomposition."""
        trace = (
            "The query asks for de Broglie wavelength.\n"
            "Looking at passage [1], the text says lambda = h/p.\n"
            "Let's derive mvr = nh / (2*pi) by equating 2*pi*r = n*lambda.\n"
            "However, note that Bohr did not explain why standing waves occur.\n"
            "In conclusion, the derivation is complete."
        )
        chunk = DocumentChunk(
            chunk_id="c1",
            doc_name="physics.pdf",
            page_num=1,
            text="lambda = h/p"
        )
        sc = ScoredChunk(chunk=chunk, rrf_score=0.03, final_rank=1)
        steps = self.engine.decompose_reasoning_steps(trace, "Explain de Broglie wavelength.", [sc])

        self.assertTrue(len(steps) >= 4)
        stages = [s.stage for s in steps]
        self.assertIn(ReasoningStage.PROBLEM_FORMULATION, stages)
        self.assertIn(ReasoningStage.EVIDENCE_CROSS_EXAM, stages)
        self.assertIn(ReasoningStage.MATHEMATICAL_DERIVATION, stages)
        self.assertIn(ReasoningStage.SYNTHESIS_CONVERGENCE, stages)

    def test_canvas_deep_thinking_markdown(self):
        """Test generating Explainer Canvas markdown for deep thinking."""
        step = ReasoningStep(
            step_number=1,
            stage=ReasoningStage.PROBLEM_FORMULATION,
            title="🎯 Problem Formulation",
            content="Deconstructing wave-particle duality premises."
        )
        trace = "Deliberating on electron momentum..."
        md = CanvasGenerator.generate_deep_thinking_markdown(trace, [step], duration_s=4.25)
        self.assertIn("Deep Reasoning & Chain-of-Thought", md)
        self.assertIn("4.25s", md)
        self.assertIn("🎯 Problem Formulation", md)
        self.assertIn("Deliberating on electron momentum...", md)

    def test_synthesis_output_wrapper(self):
        """Test SynthesisOutput string behavior and unpacking."""
        out = SynthesisOutput(
            text="Academic synthesis [1].",
            thought_trace="Thinking...",
            duration_s=2.5
        )
        # Should behave like string
        self.assertEqual(str(out), "Academic synthesis [1].")
        # Should unpack as 4-tuple
        text, trace, steps, dur = out
        self.assertEqual(text, "Academic synthesis [1].")
        self.assertEqual(trace, "Thinking...")
        self.assertEqual(dur, 2.5)

    def test_extract_thought_trace_transition_header(self):
        """Test splitting when model opens <think> and transitions directly to publication-grade synthesis."""
        raw = (
            "### <think>\n"
            "#### Problem Decomposition:\n"
            "Key entities are de Broglie wavelength and Bohr orbits.\n"
            "#### EVIDENCE CROSS-EXAMINATION:\n"
            "Passage [1] proves lambda = h/p.\n"
            "The definitive, publication-grade academic synthesis is as follows:\n\n"
            "The de Broglie wavelength formula is lambda = h/p [1]."
        )
        clean_synth, trace = extract_thought_trace(raw)
        self.assertIsNotNone(trace)
        self.assertIn("Problem Decomposition", trace)
        self.assertIn("lambda = h/p [1].", clean_synth)
        self.assertNotIn("<think>", clean_synth)
        self.assertNotIn("</think>", clean_synth)

    def test_extract_thought_trace_explicit_cot_sections(self):
        """Test general model CoT output without <think> tags."""
        raw = (
            "#### Problem Formulation:\n"
            "Deconstructing angular momentum quantization.\n"
            "#### Evidence Cross-Examination:\n"
            "Passage [1] specifies mvr = nh / (2pi).\n"
            "### Academic Synthesis:\n"
            "Electrons form standing de Broglie waves [1]."
        )
        clean_synth, trace = extract_thought_trace(raw)
        self.assertIsNotNone(trace)
        self.assertIn("Problem Formulation", trace)
        self.assertIn("standing de Broglie waves [1].", clean_synth)

    def test_decompose_reasoning_steps_explicit_headers(self):
        """Test section-based parsing for models providing markdown headers."""
        trace = (
            "#### 1. Problem Decomposition:\n"
            "Target entity is wavelength.\n"
            "#### 2. Evidence Cross-Examination:\n"
            "Passage [1] provides experimental proof.\n"
            "#### 3. Mathematical Derivation:\n"
            "mvr = nh / (2pi) => 2*pi*r = n*lambda.\n"
            "#### 4. Counter-Factual Defense:\n"
            "Ensure relativity corrections are not mistakenly applied.\n"
            "#### 5. Convergence Plan:\n"
            "Synthesize with exact [1] citations."
        )
        chunk = DocumentChunk(chunk_id="c1", doc_name="phys.pdf", page_num=1, text="lambda=h/p")
        sc = ScoredChunk(chunk=chunk, rrf_score=0.04, final_rank=1)
        steps = self.engine.decompose_reasoning_steps(trace, "query", [sc])
        self.assertEqual(len(steps), 5)
        self.assertEqual(steps[0].stage, ReasoningStage.PROBLEM_FORMULATION)
        self.assertEqual(steps[1].stage, ReasoningStage.EVIDENCE_CROSS_EXAM)
        self.assertEqual(steps[2].stage, ReasoningStage.MATHEMATICAL_DERIVATION)
        self.assertEqual(steps[3].stage, ReasoningStage.COUNTERFACTUAL_CHECK)
        self.assertEqual(steps[4].stage, ReasoningStage.SYNTHESIS_CONVERGENCE)


if __name__ == "__main__":
    unittest.main()
