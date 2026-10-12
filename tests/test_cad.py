"""
Unit and Integration Tests for privreach.cad generative CAD, FEA, and PCB subsystem.
"""

import unittest

from privreach.cad.cadquery_generator import CadQueryGenerator
from privreach.cad.sandbox_executor import SandboxCADExecutor
from privreach.cad.fea_runner import FEARunner
from privreach.cad.bionic.pattern_library import BionicPatternLibrary
from privreach.cad.pcb.kicad_generator import KiCadGenerator


class TestCADSubsystem(unittest.TestCase):
    """Verifies generative CadQuery synthesis, FEA simulation, bionic patterns, and KiCad PCB scripting."""

    def setUp(self):
        self.cad_gen = CadQueryGenerator()
        self.sandbox = SandboxCADExecutor(max_envelope_mm=(300.0, 300.0, 300.0))
        self.fea = FEARunner(material_key="aluminum_6061_t6")
        self.kicad_gen = KiCadGenerator()

    def test_cadquery_script_generation_mounting_bracket(self):
        """Generates safe parametric CadQuery script for mounting plate."""
        res = self.cad_gen.generate_mounting_bracket(length_mm=100.0, width_mm=50.0, thickness_mm=6.0)
        self.assertTrue(res.is_safe)
        self.assertTrue(res.syntax_valid)
        self.assertIn("import cadquery as cq", res.script_code)
        self.assertIn("box(length, width, thickness)", res.script_code)
        self.assertEqual(res.bounding_box_est, (100.0, 50.0, 6.0))

    def test_cadquery_script_safety_validator_rejects_malicious_code(self):
        """Rejects scripts attempting OS or subprocess command execution."""
        safe_code = "import cadquery as cq\np = cq.Workplane('XY').box(10, 10, 10)"
        is_safe, err = self.cad_gen.validate_code_safety(safe_code)
        self.assertTrue(is_safe)
        self.assertIsNone(err)

        malicious_code = "import os\nos.system('echo compromised')\nimport cadquery as cq"
        is_malicious_safe, err_malicious = self.cad_gen.validate_code_safety(malicious_code)
        self.assertFalse(is_malicious_safe)
        self.assertIn("Forbidden import", err_malicious)

    def test_sandbox_geometry_validator(self):
        """Validates positive volume, surface area, and workspace fit."""
        # 100x50x10 mm solid
        res = self.sandbox.validate_analytical_box(100.0, 50.0, 10.0, holes_volume_mm3=500.0)
        self.assertTrue(res.is_valid)
        self.assertTrue(res.is_manifold)
        self.assertEqual(res.volume_mm3, 49500.0)
        self.assertTrue(res.fits_envelope)

        # Oversized model exceeding 300mm envelope
        res_oversized = self.sandbox.validate_analytical_box(500.0, 100.0, 100.0)
        self.assertFalse(res_oversized.is_valid)
        self.assertFalse(res_oversized.fits_envelope)

    def test_fea_simulation_safe_and_failure_modes(self):
        """Calculates von Mises stress, deflection, and Factor of Safety."""
        # 1. Normal safe load: 50 N on Aluminum 6061-T6 bracket (80x30x5 mm)
        res_safe = self.fea.simulate_cantilever_bracket(
            length_mm=80.0,
            width_mm=30.0,
            thickness_mm=5.0,
            load_force_n=50.0,
            target_fos=1.5,
        )
        self.assertTrue(res_safe.is_structurally_safe)
        self.assertGreater(res_safe.factor_of_safety, 1.5)
        self.assertLess(res_safe.max_von_mises_stress_mpa, res_safe.yield_strength_mpa)
        self.assertGreater(res_safe.max_deflection_mm, 0.0)

        # 2. Extreme overload: 25,000 N -> structural failure
        res_fail = self.fea.simulate_cantilever_bracket(
            length_mm=80.0,
            width_mm=30.0,
            thickness_mm=5.0,
            load_force_n=25000.0,
            target_fos=1.5,
        )
        self.assertFalse(res_fail.is_structurally_safe)
        self.assertLess(res_fail.factor_of_safety, 1.0)

    def test_bionic_gyroid_and_honeycomb_generation(self):
        """Generates TPMS gyroid and cellular honeycomb with significant mass reduction."""
        gyroid = BionicPatternLibrary.generate_gyroid(cell_size_mm=10.0, wall_thickness_mm=1.0)
        self.assertEqual(gyroid.pattern_type, "GYROID_TPMS")
        self.assertGreater(gyroid.mass_reduction_percent, 50.0)
        self.assertIn("sin", gyroid.implicit_formula)

        honeycomb = BionicPatternLibrary.generate_honeycomb(cell_diameter_mm=8.0, wall_thickness_mm=0.8)
        self.assertEqual(honeycomb.pattern_type, "HONEYCOMB_LATTICE")
        self.assertGreater(honeycomb.mass_reduction_percent, 50.0)

    def test_kicad_pcb_script_generation(self):
        """Synthesizes valid KiCad pcbnew outline with DRC settings."""
        res = self.kicad_gen.generate_sensor_breakout_board(width_mm=45.0, height_mm=35.0)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.board_size_mm, (45.0, 35.0))
        self.assertIn("import pcbnew", res.script_code)
        self.assertIn("Edge_Cuts", res.script_code)
        self.assertEqual(res.clearance_drc_mm, 0.20)


if __name__ == "__main__":
    unittest.main()
