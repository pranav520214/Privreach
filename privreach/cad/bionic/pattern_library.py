"""
Generative Bionic Design and Lattice Infill Library.

Synthesizes Triply Periodic Minimal Surfaces (TPMS gyroids),
honeycomb structures, and bio-inspired infill patterns for structural lightweighting.
"""

from typing import Dict, List, Optional, Tuple, Any
import math
from pydantic import BaseModel, Field


class BionicPatternResult(BaseModel):
    """Specification of a synthesized bionic lightweighting pattern."""
    pattern_type: str  # "GYROID_TPMS", "SCHWARZ_PRIMITIVE", "HONEYCOMB_LATTICE"
    implicit_formula: str
    cell_size_mm: float
    wall_thickness_mm: float
    relative_density: float     # 0.0 - 1.0 (fraction of solid volume)
    mass_reduction_percent: float
    cadquery_snippet: str
    description: str


class BionicPatternLibrary:
    """
    Generates mathematical formulas and CAD code snippets for bionic lattices.
    """

    @classmethod
    def generate_gyroid(
        cls,
        cell_size_mm: float = 10.0,
        wall_thickness_mm: float = 1.0,
    ) -> BionicPatternResult:
        """
        Synthesizes a Gyroid TPMS cellular unit cell.
        Formula: sin(2pi*x/L)*cos(2pi*y/L) + sin(2pi*y/L)*cos(2pi*z/L) + sin(2pi*z/L)*cos(2pi*x/L) = t
        """
        # Approximated relative density for gyroid with thickness t and cell L
        rel_density = min(0.90, max(0.10, 1.1 * (wall_thickness_mm / cell_size_mm)))
        reduction = round((1.0 - rel_density) * 100.0, 1)

        formula = "sin(2*pi*x/L)*cos(2*pi*y/L) + sin(2*pi*y/L)*cos(2*pi*z/L) + sin(2*pi*z/L)*cos(2*pi*x/L)"
        snippet = f"""# Gyroid Infill Pattern (Cell Size: {cell_size_mm} mm, Wall: {wall_thickness_mm} mm)
# Relative Density: {rel_density:.2f} (~{reduction}% weight reduction)
L = {cell_size_mm}
t = {wall_thickness_mm}
# Implicit TPMS surface evaluated over bounding box
"""
        return BionicPatternResult(
            pattern_type="GYROID_TPMS",
            implicit_formula=formula,
            cell_size_mm=cell_size_mm,
            wall_thickness_mm=wall_thickness_mm,
            relative_density=round(rel_density, 3),
            mass_reduction_percent=reduction,
            cadquery_snippet=snippet.strip(),
            description=f"Gyroid TPMS infill delivering {reduction}% mass reduction while maintaining isotropic stiffness.",
        )

    @classmethod
    def generate_honeycomb(
        cls,
        cell_diameter_mm: float = 8.0,
        wall_thickness_mm: float = 0.8,
    ) -> BionicPatternResult:
        """
        Synthesizes a 2D/3D Hexagonal Honeycomb cellular lattice.
        Relative density: rho*/rho_s = (2 / sqrt(3)) * (t / d)
        """
        rel_density = (2.0 / math.sqrt(3.0)) * (wall_thickness_mm / cell_diameter_mm)
        rel_density = min(0.95, max(0.05, rel_density))
        reduction = round((1.0 - rel_density) * 100.0, 1)

        snippet = f"""# Hexagonal Honeycomb Infill (Diameter: {cell_diameter_mm} mm, Wall: {wall_thickness_mm} mm)
# Relative Density: {rel_density:.3f} (~{reduction}% weight reduction)
dia = {cell_diameter_mm}
wall = {wall_thickness_mm}
"""
        return BionicPatternResult(
            pattern_type="HONEYCOMB_LATTICE",
            implicit_formula="hexagonal_tessellation(r=dia/2, t=wall)",
            cell_size_mm=cell_diameter_mm,
            wall_thickness_mm=wall_thickness_mm,
            relative_density=round(rel_density, 3),
            mass_reduction_percent=reduction,
            cadquery_snippet=snippet.strip(),
            description=f"Hexagonal honeycomb core providing {reduction}% weight reduction with high out-of-plane compressive strength.",
        )
