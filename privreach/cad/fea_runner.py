"""
Finite Element Analysis (FEA) Simulation Runner.

Performs structural stress and deflection simulations under mechanical loading:
computes von Mises stress, maximum displacement, and Factor of Safety (FoS).
"""

from typing import Dict, Optional, Tuple, Any, List
import math
from pydantic import BaseModel, Field


class MaterialProperties(BaseModel):
    """Mechanical and elastic properties of an engineering material."""
    name: str
    youngs_modulus_gpa: float      # E in GPa
    yield_strength_mpa: float      # Yield stress in MPa
    poisson_ratio: float           # nu
    density_kg_m3: float           # Density


STANDARD_MATERIALS: Dict[str, MaterialProperties] = {
    "aluminum_6061_t6": MaterialProperties(
        name="Aluminum 6061-T6",
        youngs_modulus_gpa=68.9,
        yield_strength_mpa=276.0,
        poisson_ratio=0.33,
        density_kg_m3=2700.0,
    ),
    "steel_structural": MaterialProperties(
        name="Structural Steel AISI 1018",
        youngs_modulus_gpa=205.0,
        yield_strength_mpa=370.0,
        poisson_ratio=0.29,
        density_kg_m3=7850.0,
    ),
    "titanium_ti6al4v": MaterialProperties(
        name="Titanium Ti-6Al-4V Grade 5",
        youngs_modulus_gpa=113.8,
        yield_strength_mpa=880.0,
        poisson_ratio=0.34,
        density_kg_m3=4430.0,
    ),
}


class FEAResult(BaseModel):
    """Structural simulation results report."""
    material_used: str
    applied_load_n: float
    max_von_mises_stress_mpa: float
    yield_strength_mpa: float
    factor_of_safety: float
    max_deflection_mm: float
    is_structurally_safe: bool
    summary: str


class FEARunner:
    """
    Computes structural mechanics simulations for mechanical components.
    """

    def __init__(self, material_key: str = "aluminum_6061_t6"):
        self.material = STANDARD_MATERIALS.get(material_key, STANDARD_MATERIALS["aluminum_6061_t6"])

    def set_material(self, material_key: str) -> None:
        """Sets active engineering material."""
        if material_key in STANDARD_MATERIALS:
            self.material = STANDARD_MATERIALS[material_key]

    def simulate_cantilever_bracket(
        self,
        length_mm: float,
        width_mm: float,
        thickness_mm: float,
        load_force_n: float,
        target_fos: float = 1.5,
    ) -> FEAResult:
        """
        Simulates cantilever beam loading:
        - Maximum Bending Moment: M = F * L
        - Section Modulus: Z = (w * t^2) / 6
        - Bending Stress: sigma = M / Z
        - Moment of Inertia: I = (w * t^3) / 12
        - Max Tip Deflection: delta = (F * L^3) / (3 * E * I)
        """
        L = length_mm / 1000.0       # convert to meters
        w = width_mm / 1000.0
        t = thickness_mm / 1000.0
        E = self.material.youngs_modulus_gpa * 1e9  # convert to Pa

        # Maximum bending moment (N*m)
        M = load_force_n * L

        # Section modulus Z (m^3)
        Z = (w * (t ** 2)) / 6.0

        # Maximum stress (Pa -> MPa)
        sigma_pa = M / Z if Z > 0 else 0.0
        max_stress_mpa = sigma_pa / 1e6

        # Second moment of area I (m^4)
        I = (w * (t ** 3)) / 12.0

        # Deflection delta (meters -> mm)
        delta_m = (load_force_n * (L ** 3)) / (3.0 * E * I) if (E * I) > 0 else 0.0
        deflection_mm = delta_m * 1000.0

        # Factor of Safety
        yield_mpa = self.material.yield_strength_mpa
        fos = round(yield_mpa / max_stress_mpa, 2) if max_stress_mpa > 0 else 999.0

        is_safe = fos >= target_fos

        summary = (
            f"Under {load_force_n:.1f} N load, {self.material.name} bracket develops "
            f"{max_stress_mpa:.1f} MPa peak stress (Yield: {yield_mpa:.1f} MPa). "
            f"FoS = {fos:.2f} (Target: {target_fos:.1f}). Deflection: {deflection_mm:.3f} mm."
        )

        return FEAResult(
            material_used=self.material.name,
            applied_load_n=load_force_n,
            max_von_mises_stress_mpa=round(max_stress_mpa, 2),
            yield_strength_mpa=yield_mpa,
            factor_of_safety=fos,
            max_deflection_mm=round(deflection_mm, 4),
            is_structurally_safe=is_safe,
            summary=summary,
        )
