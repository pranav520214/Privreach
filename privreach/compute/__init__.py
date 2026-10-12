"""Privreach Deterministic Scientific Computing: Non-hallucinatory math with SymPy and NumPy."""

from privreach.compute.equation_parser import EquationParser
from privreach.compute.solver import DeterministicSolver
from privreach.compute.hardware_auth import HardwareBoundAuth
from privreach.compute.unit_checker import UnitChecker, DimensionCheckResult
from privreach.compute.numeric_verifier import NumericVerifier, NumericVerificationResult
from privreach.compute.z3_prover import ConstraintProver, ConstraintProofResult

__all__ = [
    "EquationParser",
    "DeterministicSolver",
    "HardwareBoundAuth",
    "UnitChecker",
    "DimensionCheckResult",
    "NumericVerifier",
    "NumericVerificationResult",
    "ConstraintProver",
    "ConstraintProofResult",
]
