"""
Generative CadQuery Script Synthesizer.

Translates engineering requirements into deterministic, parametric CadQuery
Python scripts targeting the OpenCASCADE BREP geometric modeling kernel.
"""

from typing import List, Dict, Tuple, Optional, Any
import ast
import re
from pydantic import BaseModel, Field


class CadScriptResult(BaseModel):
    """Result of synthesizing and validating a CadQuery script."""
    is_safe: bool
    script_code: str
    component_type: str
    bounding_box_est: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # (L, W, H) in mm
    features: List[str] = Field(default_factory=list)
    syntax_valid: bool = True
    error_message: Optional[str] = None


DANGEROUS_AST_CALLS = {
    "open", "exec", "eval", "compile", "__import__",
    "system", "popen", "spawn", "fork", "subprocess", "socket",
}

DANGEROUS_AST_MODULES = {
    "os", "sys", "subprocess", "shutil", "socket", "urllib", "requests",
    "http", "posix", "nt", "importlib", "builtins",
}


class CadQueryGenerator:
    """
    Synthesizes safe, auditable parametric CadQuery Python code.
    """

    def validate_code_safety(self, code_str: str) -> Tuple[bool, Optional[str]]:
        """
        Parses AST to verify the script contains zero dangerous system or network calls.
        """
        try:
            tree = ast.parse(code_str)
        except SyntaxError as e:
            return False, f"Syntax Error: {str(e)}"

        for node in ast.walk(tree):
            # Check imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_pkg = alias.name.split(".")[0]
                    if root_pkg in DANGEROUS_AST_MODULES:
                        return False, f"Forbidden import: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_pkg = node.module.split(".")[0]
                    if root_pkg in DANGEROUS_AST_MODULES:
                        return False, f"Forbidden import from: {node.module}"

            # Check function calls
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in DANGEROUS_AST_CALLS:
                        return False, f"Forbidden function call: {node.func.id}"

        return True, None

    def generate_mounting_bracket(
        self,
        length_mm: float = 80.0,
        width_mm: float = 40.0,
        thickness_mm: float = 5.0,
        hole_diameter_mm: float = 5.5,
        fillet_radius_mm: float = 3.0,
    ) -> CadScriptResult:
        """
        Generates a parametric mounting plate with 4-corner mounting holes and rounded edges.
        """
        script = f"""import cadquery as cq

# Parametric Dimensions (mm)
length = {length_mm}
width = {width_mm}
thickness = {thickness_mm}
hole_dia = {hole_diameter_mm}
fillet_r = {fillet_radius_mm}

# 1. Base Plate Extrusion
plate = (
    cq.Workplane("XY")
    .box(length, width, thickness)
    .edges("|Z")
    .fillet(fillet_r)
)

# 2. Counterbored / Through-Hole Pattern
offset_x = length / 2.0 - 10.0
offset_y = width / 2.0 - 10.0

result = (
    plate.faces(">Z")
    .workplane()
    .pushPoints([
        (offset_x, offset_y),
        (-offset_x, offset_y),
        (offset_x, -offset_y),
        (-offset_x, -offset_y),
    ])
    .hole(hole_dia)
)

# Export candidate: cq.exporters.export(result, "bracket.step")
"""
        is_safe, err = self.validate_code_safety(script)
        features = [
            f"Base box: {length_mm}x{width_mm}x{thickness_mm} mm",
            f"Corner fillets: R{fillet_radius_mm} mm",
            f"4x Mounting holes: D{hole_diameter_mm} mm",
        ]
        return CadScriptResult(
            is_safe=is_safe,
            script_code=script.strip(),
            component_type="mounting_bracket",
            bounding_box_est=(length_mm, width_mm, thickness_mm),
            features=features,
            syntax_valid=is_safe,
            error_message=err,
        )

    def generate_l_bracket(
        self,
        leg_length_a: float = 50.0,
        leg_length_b: float = 50.0,
        width: float = 30.0,
        thickness: float = 4.0,
        fillet_radius: float = 2.0,
    ) -> CadScriptResult:
        """
        Generates an L-shaped structural reinforcement bracket.
        """
        script = f"""import cadquery as cq

# Parametric L-Bracket Dimensions (mm)
leg_a = {leg_length_a}
leg_b = {leg_length_b}
w = {width}
t = {thickness}
r = {fillet_radius}

# Profile Polyline
pts = [
    (0, 0),
    (leg_a, 0),
    (leg_a, t),
    (t, t),
    (t, leg_b),
    (0, leg_b),
]

result = (
    cq.Workplane("XZ")
    .polyline(pts)
    .close()
    .extrude(w)
    .edges("|Y")
    .fillet(r)
)
"""
        is_safe, err = self.validate_code_safety(script)
        features = [
            f"L-Profile: {leg_length_a}x{leg_length_b} mm",
            f"Extrusion width: {width} mm",
            f"Wall thickness: {thickness} mm",
        ]
        return CadScriptResult(
            is_safe=is_safe,
            script_code=script.strip(),
            component_type="l_bracket",
            bounding_box_est=(leg_length_a, width, leg_length_b),
            features=features,
            syntax_valid=is_safe,
            error_message=err,
        )
