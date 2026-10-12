"""
Deterministic Numeric Verification and LLM Claim Auditor.

Cross-verifies numerical values generated in AI synthesis against exact
SymPy symbolic derivations, flagging discrepancies, precision deviations,
and order-of-magnitude hallucinations.
"""

from typing import List, Dict, Optional, Tuple, Any
import math
import re
from pydantic import BaseModel, Field


class NumericVerificationResult(BaseModel):
    """Result of comparing claimed numeric values with exact symbolic truth."""
    is_verified: bool
    claimed_value: float
    computed_value: float
    relative_error: float
    verdict: str  # "EXACT_MATCH", "WITHIN_TOLERANCE", "NUMERIC_DISCREPANCY", "ORDER_OF_MAGNITUDE_ERROR"
    tolerance: float
    audit_explanation: str


class NumericVerifier:
    """
    Compares numerical claims against exact mathematical computations.
    """

    def __init__(self, default_tolerance: float = 0.02):  # 2% standard tolerance
        self.default_tolerance = default_tolerance

    @staticmethod
    def extract_numbers_from_text(text: str) -> List[float]:
        """Extracts floating point and scientific notation numbers from text."""
        # Matches integers, decimals, and scientific notation (e.g., 3.14, 1.2e-4)
        pattern = r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?"
        raw_matches = re.findall(pattern, text)
        numbers: List[float] = []
        for m in raw_matches:
            try:
                numbers.append(float(m))
            except Exception:
                pass
        return numbers

    def verify_value(
        self,
        claimed_value: float,
        computed_value: float,
        tolerance: Optional[float] = None,
    ) -> NumericVerificationResult:
        """
        Validates whether claimed_value is mathematically consistent with computed_value.
        """
        tol = tolerance if tolerance is not None else self.default_tolerance

        # Handle zero division
        if abs(computed_value) < 1e-12:
            abs_err = abs(claimed_value - computed_value)
            is_match = abs_err < 1e-6
            return NumericVerificationResult(
                is_verified=is_match,
                claimed_value=claimed_value,
                computed_value=computed_value,
                relative_error=abs_err,
                verdict="EXACT_MATCH" if is_match else "NUMERIC_DISCREPANCY",
                tolerance=tol,
                audit_explanation=f"Near-zero comparison: absolute delta = {abs_err:.6e}",
            )

        rel_error = abs(claimed_value - computed_value) / abs(computed_value)

        # Classify verdict
        if rel_error < 1e-6:
            verdict = "EXACT_MATCH"
            is_verified = True
        elif rel_error <= tol:
            verdict = "WITHIN_TOLERANCE"
            is_verified = True
        else:
            is_verified = False
            # Check if order of magnitude error (ratio > 5 or < 0.2)
            ratio = claimed_value / computed_value if computed_value != 0 else float('inf')
            if ratio > 5.0 or ratio < 0.2 or ratio < 0:
                verdict = "ORDER_OF_MAGNITUDE_ERROR"
            else:
                verdict = "NUMERIC_DISCREPANCY"

        explanation = (
            f"Claimed {claimed_value:.5g} vs Computed {computed_value:.5g} "
            f"(relative error: {rel_error * 100:.2f}%, tolerance: {tol * 100:.1f}%). Verdict: {verdict}."
        )

        return NumericVerificationResult(
            is_verified=is_verified,
            claimed_value=claimed_value,
            computed_value=computed_value,
            relative_error=round(rel_error, 6),
            verdict=verdict,
            tolerance=tol,
            audit_explanation=explanation,
        )

    def verify_claim_against_computation(
        self,
        text_with_claim: str,
        computed_value: float,
        tolerance: Optional[float] = None,
    ) -> Optional[NumericVerificationResult]:
        """
        Scans text for the closest number to computed_value and returns verification result.
        """
        numbers = self.extract_numbers_from_text(text_with_claim)
        if not numbers:
            return None

        # Find candidate closest to computed_value
        best_candidate = min(numbers, key=lambda n: abs(n - computed_value))
        return self.verify_value(best_candidate, computed_value, tolerance=tolerance)
