"""
Deterministic Physical and Mathematical Constraint Prover.

Enforces physical parameter bounds, inequality conditions, and domain limits
(e.g., thermodynamic Carnot limits, positive absolute temperature, material yield stress).
"""

from typing import List, Dict, Tuple, Optional, Any
import sympy as sp
from pydantic import BaseModel, Field


class ConstraintProofResult(BaseModel):
    """Result of evaluating boundary constraints."""
    is_satisfied: bool
    total_constraints: int = 0
    satisfied_count: int = 0
    violated_count: int = 0
    violations: List[str] = Field(default_factory=list)
    audit_trail: List[str] = Field(default_factory=list)


class ConstraintProver:
    """
    Evaluates physical inequalities and boundary conditions.
    """

    def __init__(self):
        self.constraints: List[Tuple[str, str]] = []  # (inequality_str, description)

    def add_constraint(self, inequality_str: str, description: str = "") -> None:
        """Adds an inequality constraint (e.g., 'T > 0' or 'eta <= 1 - Tc/Th')."""
        self.constraints.append((inequality_str, description))

    def evaluate_constraints(self, variable_assignments: Dict[str, float]) -> ConstraintProofResult:
        """
        Substitutes assigned values into all registered constraints and validates consistency.
        """
        violations: List[str] = []
        audit_trail: List[str] = []
        satisfied_n = 0

        # Build substitution dictionary with SymPy symbols
        subs_dict = {sp.Symbol(k): v for k, v in variable_assignments.items()}

        for ineq_str, desc in self.constraints:
            try:
                # Parse inequality expression (e.g., "T > 0" or "sigma <= 250")
                parsed = sp.sympify(ineq_str)
                evaluated = parsed.subs(subs_dict)

                # If result simplifies to a boolean True / False
                if evaluated == sp.true or evaluated is True:
                    satisfied_n += 1
                    audit_trail.append(f"PASS: '{ineq_str}' is satisfied ({desc})")
                elif evaluated == sp.false or evaluated is False:
                    v_msg = f"VIOLATION: '{ineq_str}' failed under values {variable_assignments} ({desc})"
                    violations.append(v_msg)
                    audit_trail.append(v_msg)
                else:
                    # Could not fully evaluate (e.g. missing variables)
                    v_msg = f"UNEVALUATED: '{ineq_str}' has unassigned parameters"
                    violations.append(v_msg)
                    audit_trail.append(v_msg)
            except Exception as e:
                v_msg = f"ERROR: Failed to evaluate '{ineq_str}': {str(e)}"
                violations.append(v_msg)
                audit_trail.append(v_msg)

        total = len(self.constraints)
        is_all_passed = (len(violations) == 0) and (total > 0)

        return ConstraintProofResult(
            is_satisfied=is_all_passed,
            total_constraints=total,
            satisfied_count=satisfied_n,
            violated_count=len(violations),
            violations=violations,
            audit_trail=audit_trail,
        )
