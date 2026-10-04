"""Equation Parser: Extracts LaTeX formulas, variables, and units from research text."""

import re
from typing import List, Dict, Any, Optional, Tuple


class EquationParser:
    """
    Extracts mathematical expressions, variables, and numerical assignments
    from user queries and retrieved literature passages.
    """

    # Common scientific constants
    STANDARD_CONSTANTS: Dict[str, float] = {
        "R": 8.314462618,      # J/(mol*K) - Universal gas constant
        "R_atm": 0.082057,     # L*atm/(mol*K)
        "k_B": 1.380649e-23,   # J/K - Boltzmann constant
        "N_A": 6.02214076e23,  # 1/mol - Avogadro constant
        "h": 6.62607015e-34,   # J*s - Planck constant
        "c": 299792458.0,      # m/s - Speed of light
        "F": 96485.33212,      # C/mol - Faraday constant
        "g": 9.80665,          # m/s^2 - Standard gravity
        "pi": 3.141592653589793,
    }

    @staticmethod
    def extract_equations(text: str) -> List[str]:
        """Extract LaTeX equations or algebraic equalities from text."""
        equations: List[str] = []

        # 1. LaTeX math blocks $$ ... $$ or \[ ... \]
        latex_display = re.findall(r'\$\$(.+?)\$\$|\\\[(.+?)\\\]', text, flags=re.DOTALL)
        for g1, g2 in latex_display:
            eq = (g1 or g2).strip()
            if "=" in eq:
                equations.append(eq)

        # 2. Inline LaTeX $ ... $ or \( ... \)
        latex_inline = re.findall(r'\$(.+?)\$|\\\((.+?)\\\)', text)
        for g1, g2 in latex_inline:
            eq = (g1 or g2).strip()
            if "=" in eq and len(eq) >= 3:
                equations.append(eq)

        # 3. Plain text equations like PV = nRT or G = H - T*S
        plain_eqs = re.findall(r'(?:[A-Za-z_][A-Za-z0-9_]*\s*=\s*[A-Za-z0-9_+\-*/\^().\s]{2,})', text)
        for eq in plain_eqs:
            clean = eq.strip()
            # Filter out non-math code or assignments
            if clean and not clean.startswith(("def ", "class ", "import ", "for ", "if ")):
                if len(clean) > 3 and clean not in equations:
                    equations.append(clean)

        return equations

    @staticmethod
    def extract_variable_assignments(text: str) -> Dict[str, float]:
        """
        Extract numerical variable assignments from text.
        e.g., 'T = 298.15 K', 'P = 2.5 atm', 'n = 3 moles', 'V = 0.5 L'
        """
        assignments: Dict[str, float] = {}

        # Pattern: Var = Number [Unit]
        pattern = r'(?:\b([A-Za-z][A-Za-z0-9_]*)\s*[:=]\s*([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*([a-zA-Z/°μΩ%]*))'
        matches = re.findall(pattern, text)

        for var_name, num_str, unit in matches:
            try:
                val = float(num_str)
                assignments[var_name] = val
            except ValueError:
                continue

        # Look for explicit natural language expressions: 'temperature of 300 K', 'pressure of 1.5 atm'
        keyword_map = {
            "temperature": "T",
            "pressure": "P",
            "volume": "V",
            "moles": "n",
            "mass": "m",
            "energy": "E",
            "enthalpy": "H",
            "entropy": "S",
            "time": "t",
            "velocity": "v",
            "frequency": "nu"
        }

        for kw, symbol in keyword_map.items():
            if symbol not in assignments:
                m = re.search(rf'{kw}\s+(?:of|is|=|:)\s+([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)', text, re.IGNORECASE)
                if m:
                    try:
                        assignments[symbol] = float(m.group(1))
                    except ValueError:
                        pass

        return assignments

    @classmethod
    def resolve_constants(cls, variables: Dict[str, float]) -> Dict[str, float]:
        """Supplement variables with standard constants if referenced but not provided."""
        resolved = dict(variables)
        for const_name, const_val in cls.STANDARD_CONSTANTS.items():
            if const_name not in resolved:
                resolved[const_name] = const_val
        return resolved

    @staticmethod
    def extract_numbers(text: str) -> List[float]:
        """Extract all floating point or integer numbers mentioned in a string."""
        raw_nums = re.findall(r'[+-]?\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b', text)
        results = []
        for n in raw_nums:
            try:
                results.append(float(n))
            except ValueError:
                pass
        return results
