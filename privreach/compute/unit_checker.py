"""
Deterministic Physical Dimensional Unit Checker.

Enforces physical unit homogeneity and dimensional consistency across equations
using SI base dimension analysis: [M] (mass), [L] (length), [T] (time),
[I] (current), [Theta] (temperature), [N] (substance), [J] (luminosity).
"""

from typing import List, Dict, Tuple, Optional, Any
import sympy as sp
from sympy.physics.units import (
    meter, second, kilogram, ampere, kelvin, mole, candela,
    newton, joule, watt, pascal, volt, ohm, hertz, coulomb,
)
from sympy.physics.units.systems.si import SI
from pydantic import BaseModel, Field


class DimensionCheckResult(BaseModel):
    """Result of physical dimension homogeneity validation."""
    is_valid: bool
    is_homogeneous: bool
    lhs_dimension: str = ""
    rhs_dimension: str = ""
    error_message: Optional[str] = None
    audit_trail: str = ""


UNIT_LOOKUP: Dict[str, sp.Expr] = {
    # Base SI units
    "m": meter, "meter": meter, "meters": meter,
    "s": second, "sec": second, "second": second, "seconds": second,
    "kg": kilogram, "kilogram": kilogram, "kilograms": kilogram,
    "a": ampere, "amp": ampere, "ampere": ampere, "amperes": ampere,
    "k": kelvin, "kelvin": kelvin,
    "mol": mole, "mole": mole, "moles": mole,
    "cd": candela, "candela": candela,

    # Derived SI units
    "n": newton, "newton": newton, "newtons": newton,
    "j": joule, "joule": joule, "joules": joule,
    "w": watt, "watt": watt, "watts": watt,
    "pa": pascal, "pascal": pascal,
    "v": volt, "volt": volt, "volts": volt,
    "ohm": ohm, "ohms": ohm,
    "hz": hertz, "hertz": hertz,
    "c": coulomb, "coulomb": coulomb,
}


class UnitChecker:
    """
    Validates that physical equations obey dimensional homogeneity.
    """

    @classmethod
    def get_unit_expr(cls, unit_str: str) -> Optional[sp.Expr]:
        """Resolves unit string (e.g. 'kg*m/s^2' or 'newton') to SymPy unit expression."""
        clean = unit_str.strip().lower().replace("^", "**")
        if clean in UNIT_LOOKUP:
            return UNIT_LOOKUP[clean]

        # Attempt to parse composite unit expression
        local_dict = {k: v for k, v in UNIT_LOOKUP.items()}
        try:
            return sp.sympify(clean, locals=local_dict)
        except Exception:
            return None

    @classmethod
    def get_dimensional_string(cls, unit_or_expr: Any) -> str:
        """Computes canonical dimensional string representation (e.g., mass*length/time**2)."""
        try:
            dim_expr = SI.get_dimensional_expr(unit_or_expr)
            dim_sys = SI.get_dimension_system()
            deps = dim_sys.get_dimensional_dependencies(dim_expr)
            if deps:
                terms = []
                for k, v in sorted(deps.items(), key=lambda x: str(x[0])):
                    name = str(k).replace("Dimension(", "").replace(")", "")
                    terms.append(f"{name}**{v}" if v != 1 else name)
                return "*".join(terms)
            return str(sp.simplify(dim_expr))
        except Exception:
            return str(unit_or_expr)

    def check_equation_homogeneity(
        self,
        equation_str: str,
        variable_units: Dict[str, str],
    ) -> DimensionCheckResult:
        """
        Validates that both sides of an equation have identical physical dimensions.
        Example:
            equation_str = "F = m * a"
            variable_units = {"F": "newton", "m": "kg", "a": "m/s^2"}
        """
        if "=" not in equation_str:
            return DimensionCheckResult(
                is_valid=False,
                is_homogeneous=False,
                error_message="Missing '=' operator in equation string",
            )

        lhs_str, rhs_str = equation_str.split("=", 1)
        lhs_str = lhs_str.strip()
        rhs_str = rhs_str.strip()

        # Build substitution map with resolved unit expressions
        subs_map: Dict[sp.Symbol, sp.Expr] = {}
        local_vars: Dict[str, sp.Symbol] = {}
        for var_name, u_str in variable_units.items():
            sym = sp.Symbol(var_name)
            local_vars[var_name] = sym
            u_expr = self.get_unit_expr(u_str)
            if u_expr is not None:
                subs_map[sym] = u_expr

        try:
            lhs_expr = sp.sympify(lhs_str, locals=local_vars)
            rhs_expr = sp.sympify(rhs_str, locals=local_vars)

            lhs_with_units = lhs_expr.subs(subs_map)
            rhs_with_units = rhs_expr.subs(subs_map)

            lhs_dim = self.get_dimensional_string(lhs_with_units)
            rhs_dim = self.get_dimensional_string(rhs_with_units)

            # Decompose dimensions down to base SI dependencies (Mass, Length, Time, etc.)
            dim_system = SI.get_dimension_system()
            dim_lhs_sp = SI.get_dimensional_expr(lhs_with_units)
            dim_rhs_sp = SI.get_dimensional_expr(rhs_with_units)

            deps_lhs = dim_system.get_dimensional_dependencies(dim_lhs_sp)
            deps_rhs = dim_system.get_dimensional_dependencies(dim_rhs_sp)

            is_match = (deps_lhs == deps_rhs) or (dim_lhs_sp == dim_rhs_sp)

            if is_match:
                audit = f"Dimensionally consistent: LHS [{lhs_dim}] matches RHS [{rhs_dim}]."
                return DimensionCheckResult(
                    is_valid=True,
                    is_homogeneous=True,
                    lhs_dimension=lhs_dim,
                    rhs_dimension=rhs_dim,
                    audit_trail=audit,
                )
            else:
                err = f"Dimensional mismatch: LHS has [{lhs_dim}], but RHS has [{rhs_dim}]."
                return DimensionCheckResult(
                    is_valid=True,
                    is_homogeneous=False,
                    lhs_dimension=lhs_dim,
                    rhs_dimension=rhs_dim,
                    error_message=err,
                    audit_trail=err,
                )
        except Exception as e:
            return DimensionCheckResult(
                is_valid=False,
                is_homogeneous=False,
                error_message=f"Evaluation error: {str(e)}",
            )
