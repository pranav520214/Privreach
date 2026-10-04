"""Unit & Integration Tests for Phase 2: Deterministic Scientific Compute & Tool Graph Bus."""

import os
import shutil
import unittest
import numpy as np
import sympy as sp

from privearch.schemas import (
    ToolCallResult,
    VerificationStatus,
    CalculationVerification,
    ArtifactType,
    ArtifactRecord,
)
from privearch.tools.base import BaseToolAdapter
from privearch.tools.python_sandbox import PythonSandboxAdapter
from privearch.tools.tool_graph import ToolGraph
from privearch.compute.equation_parser import EquationParser
from privearch.compute.solver import DeterministicSolver
from privearch.artifacts.registry import ArtifactRegistry


class TestPhase2Compute(unittest.TestCase):
    """Test suite verifying all Phase 2 scientific computing deliverables."""

    def setUp(self):
        self.test_artifacts_dir = ".test_privearch_artifacts"
        os.makedirs(self.test_artifacts_dir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.test_artifacts_dir):
            shutil.rmtree(self.test_artifacts_dir, ignore_errors=True)

    # -------------------------------------------------------------
    # 1. Tool Graph & Python Sandbox Tests
    # -------------------------------------------------------------
    def test_python_sandbox_evaluation(self):
        """Test deterministic evaluation of math and SymPy expressions."""
        sandbox = PythonSandboxAdapter(default_timeout=5.0)
        self.assertTrue(sandbox.is_available())

        # Mathematical expression
        res = sandbox.evaluate_expression("sp.sin(sp.pi / 2) + 3.0")
        self.assertTrue(res.success, msg=f"Error: {res.error}")
        self.assertAlmostEqual(float(res.output), 4.0, places=4)

        # Variables substitution
        res_vars = sandbox.evaluate_expression("m * c**2", variables={"m": 2.0, "c": 3.0})
        self.assertTrue(res_vars.success)
        self.assertAlmostEqual(float(res_vars.output), 18.0, places=4)

    def test_python_sandbox_security_auditor(self):
        """Verify AST auditor prevents dangerous operations and imports."""
        sandbox = PythonSandboxAdapter(strict_sandbox=True)

        # Attempt to import socket
        res_socket = sandbox.execute({"code": "import socket\ns = socket.socket()"})
        self.assertFalse(res_socket.success)
        self.assertIn("Security Violation", res_socket.error)

        # Attempt to call os.system
        res_os = sandbox.execute({"code": "import os\nos.system('echo test')"})
        self.assertFalse(res_os.success)
        self.assertIn("Security Violation", res_os.error)

    def test_python_sandbox_timeout(self):
        """Verify execution timeout prevents infinite loops."""
        sandbox = PythonSandboxAdapter(default_timeout=1.0)
        res = sandbox.execute({"code": "import time\ntime.sleep(3.0)", "timeout": 1.0})
        self.assertFalse(res.success)
        self.assertIn("timed out", res.error)

    def test_tool_graph_registry(self):
        """Test ToolGraph registration, discovery, and execution dispatch."""
        tg = ToolGraph(register_defaults=True)
        tools = tg.list_tools()
        tool_names = [t["name"] for t in tools]
        self.assertIn("python_sandbox", tool_names)

        # Dispatch via graph
        res = tg.execute("python_sandbox", {"code": "import numpy as np; _ans = float(np.sqrt(144))", "return_variables": ["_ans"]})
        self.assertTrue(res.success)
        self.assertAlmostEqual(float(res.output), 12.0, places=4)

    # -------------------------------------------------------------
    # 2. Equation Parser Tests
    # -------------------------------------------------------------
    def test_equation_and_variable_extraction(self):
        """Verify equation parsing from LaTeX and natural language."""
        sample_text = (
            "The ideal gas equation is $$P*V = n*R*T$$. "
            "For a container at temperature T = 300.0 K, with pressure P = 101325.0 Pa, "
            "and n = 2.0 moles, calculate the volume."
        )

        eqs = EquationParser.extract_equations(sample_text)
        self.assertTrue(len(eqs) >= 1)
        self.assertIn("P*V = n*R*T", eqs[0])

        vars_dict = EquationParser.extract_variable_assignments(sample_text)
        self.assertIn("T", vars_dict)
        self.assertEqual(vars_dict["T"], 300.0)
        self.assertEqual(vars_dict["n"], 2.0)
        self.assertEqual(vars_dict["P"], 101325.0)

    # -------------------------------------------------------------
    # 3. Deterministic Solver & Audit Tests
    # -------------------------------------------------------------
    def test_solver_symbolic_and_numeric(self):
        """Verify SymPy symbolic isolate and numeric calculation."""
        solver = DeterministicSolver()
        val, formula, code = solver.solve_equation(
            equation_str="P*V = n*R*T",
            target_variable="V",
            known_values={"P": 101325.0, "n": 1.0, "T": 273.15}
        )
        self.assertIsNotNone(val)
        # Expected V ~ 0.022414 m^3
        self.assertAlmostEqual(val, 0.022414, places=4)
        self.assertIn("V =", formula)

    def test_solver_verification_truth_vs_hallucination(self):
        """Verify deterministic audit confirms truth and catches hallucination."""
        solver = DeterministicSolver()
        knowns = {"P": 101325.0, "n": 2.0, "T": 300.0}

        # Case A: Model predicts correct number
        audit_true = solver.verify_calculation(
            equation_str="P*V = n*R*T",
            target_variable="V",
            known_values=knowns,
            model_claimed_text="The calculated volume is approximately 0.0492 cubic meters."
        )
        self.assertTrue(audit_true.is_verified)
        self.assertEqual(audit_true.verification_status, VerificationStatus.VERIFIED)

        # Case B: Model hallucinates an incorrect number (0.25)
        audit_false = solver.verify_calculation(
            equation_str="P*V = n*R*T",
            target_variable="V",
            known_values=knowns,
            model_claimed_text="The calculated volume is 0.25 cubic meters."
        )
        self.assertFalse(audit_false.is_verified)
        self.assertEqual(audit_false.verification_status, VerificationStatus.CONTRADICTED)
        self.assertIn("DISCREPANCY", audit_false.verification_details)

    # -------------------------------------------------------------
    # 4. Artifact Registry & Provenance Tests
    # -------------------------------------------------------------
    def test_artifact_provenance_lifecycle(self):
        """Verify artifact persistence and provenance chain."""
        reg = ArtifactRegistry(storage_dir=self.test_artifacts_dir)
        art = reg.save_calculation(
            name="Molar Volume at STP",
            equation="P*V = n*R*T",
            variables={"P": 101325.0, "T": 273.15, "n": 1.0},
            computed_value=0.022414,
            code_executed="ans = 0.022414",
            source_doc="Chemistry_NCERT_Part1.pdf",
            source_page=14,
            description="Molar volume derivation"
        )

        self.assertIsNotNone(art.artifact_id)
        self.assertEqual(art.artifact_type, ArtifactType.CALCULATION)
        self.assertTrue(os.path.exists(art.file_path))
        self.assertIn("proof_chain", art.provenance)
        self.assertIn("Chemistry_NCERT_Part1.pdf (p.14)", art.provenance["proof_chain"])

        # Reload manifest from disk and verify persistence
        reg2 = ArtifactRegistry(storage_dir=self.test_artifacts_dir)
        loaded = reg2.get(art.artifact_id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.name, "Molar Volume at STP")


if __name__ == "__main__":
    unittest.main()
