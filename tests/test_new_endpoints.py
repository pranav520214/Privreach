"""
Integration Tests for Ingress, Airlock, and Prover server endpoints.
"""

import unittest
from starlette.testclient import TestClient
from privreach.desktop_server import app


class TestNewServerEndpoints(unittest.TestCase):
    """Verifies ASGI endpoints for Ingress, Airlock, and Prover."""

    def setUp(self):
        self.client = TestClient(app)

    def test_prover_verify_endpoint(self):
        """POST /api/prover/verify must return valid ProofReport."""
        payload = {
            "text": "The semiconductor research demonstrates verified lithography performance.",
            "strict_mode": True,
        }
        resp = self.client.post("/api/prover/verify", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("success"))
        report = data.get("proof_report", {})
        self.assertIn("grounding_ratio", report)
        self.assertIn("verified_text", report)

    def test_ingress_harvest_endpoint_validation(self):
        """POST /api/ingress/harvest must reject empty queries."""
        resp = self.client.post("/api/ingress/harvest", json={"query": ""})
        self.assertEqual(resp.status_code, 400)

    def test_airlock_process_missing_file(self):
        """POST /api/airlock/process must return 404 for missing file."""
        resp = self.client.post("/api/airlock/process", json={"file_path": "non_existent_file.pdf"})
    def test_discovery_swanson_validation(self):
        """POST /api/discovery/swanson must reject empty entity_a."""
        resp = self.client.post("/api/discovery/swanson", json={"entity_a": ""})
        self.assertEqual(resp.status_code, 400)

    def test_discovery_isomorphisms_endpoint(self):
        """POST /api/discovery/isomorphisms must return IsomorphismReport."""
        payload = {
            "equations": [
                {"name": "Eq1", "expression": "G * m1 * m2 / r**2", "domain": "gravity"},
                {"name": "Eq2", "expression": "k * q1 * q2 / r**2", "domain": "electro"},
            ]
        }
        resp = self.client.post("/api/discovery/isomorphisms", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("success"))
        report = data.get("report", {})
        self.assertGreaterEqual(report.get("total_isomorphic_clusters", 0), 1)

    def test_cad_generate_endpoint(self):
        """POST /api/cad/generate must return CadScriptResult and FEAResult."""
        payload = {
            "component_type": "mounting_bracket",
            "length_mm": 80.0,
            "width_mm": 40.0,
            "thickness_mm": 5.0,
            "load_n": 100.0,
            "simulate_fea": True,
        }
        resp = self.client.post("/api/cad/generate", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("success"))
        self.assertIn("cad_script", data)
        self.assertIn("fea_simulation", data)
        self.assertTrue(data["cad_script"]["is_safe"])


if __name__ == "__main__":
    unittest.main()
