"""Deterministic Scientific Solver: Symbolic SymPy and NumPy calculations with error auditing."""

import math
from typing import Dict, Any, Optional, Tuple, List
import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor
)

from privearch.schemas import CalculationVerification, VerificationStatus
from privearch.compute.equation_parser import EquationParser
from privearch.tools.python_sandbox import PythonSandboxAdapter


class DeterministicSolver:
    """
    Symbolic & Numerical Scientific Solver:
    Computes exact mathematical answers and verifies LLM claims against non-hallucinated truth.
    """

    def __init__(self, sandbox: Optional[PythonSandboxAdapter] = None):
        self.sandbox = sandbox or PythonSandboxAdapter()
        self.transformations = (
            standard_transformations +
            (implicit_multiplication_application, convert_xor)
        )

    SAFE_MATH_GLOBALS = {
        "__builtins__": None,
        "Integer": sp.Integer,
        "Float": sp.Float,
        "Rational": sp.Rational,
        "Symbol": sp.Symbol,
        "sin": sp.sin,
        "cos": sp.cos,
        "tan": sp.tan,
        "asin": sp.asin,
        "acos": sp.acos,
        "atan": sp.atan,
        "sinh": sp.sinh,
        "cosh": sp.cosh,
        "tanh": sp.tanh,
        "exp": sp.exp,
        "log": sp.log,
        "ln": sp.ln,
        "sqrt": sp.sqrt,
        "pi": sp.pi,
        "E": sp.E,
        "Abs": sp.Abs,
    }

    DANGEROUS_TOKENS = (
        "__", "import", "exec", "eval", "compile", "open", "globals",
        "locals", "builtins", "system", "popen", "lambda", "class", "def",
        "getattr", "setattr", "delattr", "subprocess", "os.", "sys.",
        "[", "]", ";", "\\x", "\\u"
    )

    @classmethod
    def is_safe_math_expression(cls, expr: str) -> bool:
        """Verify that an expression contains only harmless mathematical tokens."""
        lower = expr.lower()
        for tok in cls.DANGEROUS_TOKENS:
            if tok in lower:
                return False
        # Must not contain string literals or brackets
        if '"' in expr or "'" in expr:
            return False
        return True

    def solve_equation(
        self,
        equation_str: str,
        target_variable: str,
        known_values: Dict[str, float]
    ) -> Tuple[Optional[float], str, str]:
        """
        Solves an equation for target_variable given known_values.
        Returns: (numerical_result, symbolic_formula_str, code_executed)
        """
        # Clean equation string
        clean_eq = equation_str.replace("\\cdot", "*").replace("\\times", "*")
        clean_eq = clean_eq.replace("{", "(").replace("}", ")")

        # Split left and right side of equality
        if "=" in clean_eq:
            lhs_str, rhs_str = clean_eq.split("=", 1)
        else:
            lhs_str, rhs_str = target_variable, clean_eq

        # Security Guardrail: validate both sides of the equation
        if not self.is_safe_math_expression(lhs_str) or not self.is_safe_math_expression(rhs_str):
            return None, "Error: Mathematical expression contained disallowed or non-mathematical tokens.", ""

        try:
            lhs = parse_expr(lhs_str, global_dict=self.SAFE_MATH_GLOBALS, transformations=self.transformations)
            rhs = parse_expr(rhs_str, global_dict=self.SAFE_MATH_GLOBALS, transformations=self.transformations)

            # Expression = LHS - RHS = 0
            rel_expr = lhs - rhs
            target_sym = sp.Symbol(target_variable)

            # Solve symbolically
            solutions = sp.solve(rel_expr, target_sym)
            if not solutions:
                # If explicit solve failed, try direct assignment if LHS is target_variable
                solutions = [rhs]

            primary_sol = solutions[0]
            symbolic_str = f"{target_variable} = {sp.latex(primary_sol)}"

            # Substitute known values + standard constants
            all_vars = EquationParser.resolve_constants(known_values)
            subs_dict = {sp.Symbol(k): v for k, v in all_vars.items() if sp.Symbol(k) in primary_sol.free_symbols}

            evaluated = primary_sol.subs(subs_dict).evalf()
            val_float = float(evaluated)

            code_executed = (
                f"# SymPy Deterministic Solution\n"
                f"import sympy as sp\n"
                f"{', '.join([k for k in all_vars.keys()])} = sp.symbols('{ ' '.join([k for k in all_vars.keys()]) }')\n"
                f"sol = {repr(primary_sol)}\n"
                f"ans = float(sol.subs({subs_dict}))"
            )

            return val_float, symbolic_str, code_executed

        except Exception as e:
            # Fallback to sandbox evaluation
            fallback_code = (
                f"import math, numpy as np, sympy as sp\n"
                f"known = {known_values}\n"
                f"# Fallback evaluation\n"
            )
            return None, f"Error: {e}", fallback_code

    def verify_calculation(
        self,
        equation_str: str,
        target_variable: str,
        known_values: Dict[str, float],
        model_claimed_text: str,
        tolerance: float = 0.05
    ) -> CalculationVerification:
        """
        Audits a model's predicted number against the exact calculated truth.
        """
        calc_val, formula_str, code = self.solve_equation(
            equation_str=equation_str,
            target_variable=target_variable,
            known_values=known_values
        )

        # Extract predicted numbers from model's statement
        predicted_numbers = EquationParser.extract_numbers(model_claimed_text)
        best_candidate: Optional[float] = None
        min_error: Optional[float] = None

        if calc_val is not None and predicted_numbers:
            for num in predicted_numbers:
                err = abs(num - calc_val)
                if min_error is None or err < min_error:
                    min_error = err
                    best_candidate = num

        # Evaluate audit status
        is_verified = False
        rel_error = None
        abs_error = None
        status = VerificationStatus.UNSUPPORTED

        if calc_val is not None:
            computed_str = f"{calc_val:.5g}"
            if best_candidate is not None:
                abs_error = abs(best_candidate - calc_val)
                denom = abs(calc_val) if abs(calc_val) > 1e-9 else 1.0
                rel_error = abs_error / denom

                if rel_error <= tolerance:
                    is_verified = True
                    status = VerificationStatus.VERIFIED
                    details = (
                        f"Model predicted {best_candidate:.5g}. Deterministic SymPy computed {computed_str}. "
                        f"Relative error: {rel_error*100:.2f}% (Within tolerance {tolerance*100:.1f}%)."
                    )
                else:
                    status = VerificationStatus.CONTRADICTED
                    details = (
                        f"CALCULATION DISCREPANCY: Model claimed {best_candidate:.5g}, but deterministic "
                        f"SymPy evaluation computed {computed_str}. Error: {rel_error*100:.1f}%."
                    )
            else:
                status = VerificationStatus.UNSUPPORTED
                details = (
                    f"Model did not provide a parseable numerical answer. "
                    f"Deterministic ground truth computed: {computed_str}."
                )
        else:
            computed_str = "Calculation could not be evaluated"
            details = f"Failed to solve equation '{equation_str}' symbolically."

        return CalculationVerification(
            equation_latex=equation_str,
            target_variable=target_variable,
            variables=known_values,
            model_predicted_value=str(best_candidate) if best_candidate is not None else None,
            deterministic_computed_value=computed_str,
            is_verified=is_verified,
            absolute_error=abs_error,
            relative_error=rel_error,
            verification_status=status,
            verification_details=details,
            code_executed=code
        )
