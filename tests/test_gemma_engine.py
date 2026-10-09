"""Unit & Integration tests for Embedded Google Gemma 3 1B IT Inference Engine."""

import os
import unittest
from privreach.models.gemma_engine import GemmaInProcessEngine
from privreach.models.client import LocalModelClient


class TestGemmaEngine(unittest.TestCase):
    def setUp(self):
        self.engine = GemmaInProcessEngine.get_instance()

    def test_gemma_model_discovered(self):
        """Verify model weights are found and valid."""
        path = self.engine.model_path
        self.assertIsNotNone(path, "Gemma 3 GGUF weights path must be discovered.")
        self.assertTrue(os.path.exists(path), f"Gemma weights must exist on disk at {path}")
        self.assertGreater(os.path.getsize(path), 500_000_000, "Weights must be > 500MB")

    def test_gemma_is_available(self):
        """Verify engine reports available when weights and llama_cpp exist."""
        self.assertTrue(self.engine.is_available())

    def test_gemma_status_dict(self):
        """Verify engine status reporting."""
        status = self.engine.get_status()
        self.assertEqual(status["engine"], "in_process_gemma3")
        self.assertEqual(status["model_name"], "google/gemma-3-1b-it")
        self.assertTrue(status["available"])
        self.assertIn("weights_path", status)

    def test_gemma_inference_generation(self):
        """Verify deterministic generation with Gemma 3 1B IT in-process."""
        response = self.engine.generate("Output the number 42 and nothing else.", max_tokens=16)
        self.assertIn("42", response)

    def test_local_model_client_routing(self):
        """Verify LocalModelClient transparently routes to Gemma in-process without Ollama."""
        client = LocalModelClient()
        self.assertTrue(client.is_available())
        models = client.list_models()
        self.assertIn("google/gemma-3-1b-it", models)
        out = client.generate("google/gemma-3-1b-it", "Reply with 'Privearch OK'", max_tokens=16)
        self.assertTrue(len(out) > 0)
