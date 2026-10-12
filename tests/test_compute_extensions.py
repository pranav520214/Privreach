"""
Unit and Integration Tests for privreach.compute extensions.
"""

import unittest
from privreach.compute.unit_checker import UnitChecker
from privreach.compute.numeric_verifier import NumericVerifier
from privreach.compute.z3_prover import ConstraintProver


class TestComputeExtensions(unittest.TestCase):
    """Verifies deterministic dimensional unit checking, numeric verification, and constraint proving."""

    def setUp(self):
        self.unit_checker = UnitChecker()
        self.numeric_verifier = NumericVerifier(default_tolerance=0.02)
        self.constraint_prover = ConstraintProver()

    def test_dimensional_homogeneity_newton_second_law(self):
        """F = m * a must have matching dimensions on LHS and RHS ([mass]*[length]/[time]**2)."""
        equation = "F = m * a"
        units = {"F": "newton", "m": "kg", "a": "m/s**2"}

        res = self.unit_checker.check_equation_homogeneity(equation, units)
        self.assertTrue(res.is_valid)
        self.assertTrue(res.is_homogeneous)
        self.assertIn("mass", res.lhs_dimension)
        self.assertIn("length", res.lhs_dimension)

    def test_dimensional_homogeneity_kinetic_energy(self):
        """E = 0.5 * m * v**2 must dimensionally equate to joules."""
        equation = "E = m * (v**2)"
        units = {"E": "joule", "m": "kg", "v": "m/s"}

        res = self.unit_checker.check_equation_homogeneity(equation, units)
        self.assertTrue(res.is_valid)
        self.assertTrue(res.is_homogeneous)

    def test_dimensional_mismatch_detected(self):
        """F = m * v is dimensionally invalid (Force != Momentum)."""
        equation = "F = m * v"
        units = {"F": "newton", "m": "kg", "v": "m/s"}

        res = self.unit_checker.check_equation_homogeneity(equation, units)
        self.assertTrue(res.is_valid)
        self.assertFalse(res.is_homogeneous)
        self.assertIsNotNone(res.error_message)

    def test_numeric_verifier_exact_and_within_tolerance(self):
        """Verifies exact matches and tolerances within 2%."""
        # Exact match
        res_exact = self.numeric_verifier.verify_value(claimed_value=42.0, computed_value=42.0)
        self.assertTrue(res_exact.is_verified)
        self.assertEqual(res_exact.verdict, "EXACT_MATCH")

        # 1% difference within 2% tolerance
        res_tol = self.numeric_verifier.verify_value(claimed_value=101.0, computed_value=100.0)
        self.assertTrue(res_tol.is_verified)
        self.assertEqual(res_tol.verdict, "WITHIN_TOLERANCE")

    def test_numeric_verifier_discrepancy_and_order_of_magnitude(self):
        """Flags discrepancies and order-of-magnitude hallucinations."""
        # Discrepancy (15% error)
        res_disc = self.numeric_verifier.verify_value(claimed_value=115.0, computed_value=100.0)
        self.assertFalse(res_disc.is_verified)
        self.assertEqual(res_disc.verdict, "NUMERIC_DISCREPANCY")

        # Order of magnitude error (10x)
        res_oom = self.numeric_verifier.verify_value(claimed_value=1000.0, computed_value=10.0)
        self.assertFalse(res_oom.is_verified)
        self.assertEqual(res_oom.verdict, "ORDER_OF_MAGNITUDE_ERROR")

    def test_numeric_extraction_from_sentence(self):
        """Extracts closest candidate number from synthesis sentence."""
        sentence = "The calculated resonant frequency of the cavity is 4.35 GHz with 0.12 losses."
        res = self.numeric_verifier.verify_claim_against_computation(
            text_with_claim=sentence,
            computed_value=4.32,
            tolerance=0.02,
        )
        self.assertIsNotNone(res)
        self.assertTrue(res.is_verified)
        self.assertEqual(res.claimed_value, 4.35)

    def test_constraint_prover_carnot_limit(self):
        """Validates that thermodynamic efficiency obeys the Carnot theorem limit."""
        # Carnot limit: eta <= 1 - Tc / Th
        self.constraint_prover.add_constraint("eta <= 1 - Tc / Th", "Carnot thermodynamic limit")
        self.constraint_prover.add_constraint("Tc > 0", "Absolute temperature positive")
        self.constraint_prover.add_constraint("Th > Tc", "Heat source hotter than sink")

        # Satisfying assignment: Tc=300K, Th=600K -> Carnot limit = 0.5. eta = 0.4 <= 0.5 -> PASS
        valid_res = self.constraint_prover.evaluate_constraints({"eta": 0.40, "Tc": 300.0, "Th": 600.0})
        self.assertTrue(valid_res.is_satisfied)
        self.assertEqual(valid_res.violated_count, 0)

        # Violating assignment: eta = 0.70 > 0.5 -> VIOLATION
        invalid_res = self.constraint_prover.evaluate_constraints({"eta": 0.70, "Tc": 300.0, "Th": 600.0})
        self.assertFalse(invalid_res.is_satisfied)
        self.assertEqual(invalid_res.violated_count, 1)


if __name__ == "__main__":
    unittest.main()
