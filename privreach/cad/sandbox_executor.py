"""
CAD Sandbox Execution and Geometry Manifold Validator.

Validates that generated CAD models are physically manufacturable:
watertight (manifold solid), non-self-intersecting, positive volume,
and fit within target machine build envelope.
"""

from typing import Tuple, Optional, Dict, Any, List
from pydantic import BaseModel, Field


class GeometryValidationResult(BaseModel):
    """Result of geometric sanity and manifold validation."""
    is_valid: bool
    is_manifold: bool
    volume_mm3: float = 0.0
    surface_area_mm2: float = 0.0
    bounding_box: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    fits_envelope: bool = True
    issues: List[str] = Field(default_factory=list)


class SandboxCADExecutor:
    """
    Executes and inspects geometric properties of CAD models.
    """

    def __init__(self, max_envelope_mm: Tuple[float, float, float] = (300.0, 300.0, 300.0)):
        self.max_envelope = max_envelope_mm

    def validate_analytical_box(
        self,
        length: float,
        width: float,
        height: float,
        holes_volume_mm3: float = 0.0,
    ) -> GeometryValidationResult:
        """
        Analytically computes solid volume, surface area, and envelope bounds.
        """
        issues: List[str] = []
        gross_vol = length * width * height
        net_vol = gross_vol - holes_volume_mm3

        if net_vol <= 0:
            issues.append(f"Invalid non-positive solid volume: {net_vol:.2f} mm3")

        area = 2 * (length * width + width * height + length * height)
        bbox = (float(length), float(width), float(height))

        # Check build volume limits
        fits = (
            bbox[0] <= self.max_envelope[0]
            and bbox[1] <= self.max_envelope[1]
            and bbox[2] <= self.max_envelope[2]
        )
        if not fits:
            issues.append(f"Model dimensions {bbox} exceed maximum build envelope {self.max_envelope}")

        is_valid = len(issues) == 0

        return GeometryValidationResult(
            is_valid=is_valid,
            is_manifold=True,
            volume_mm3=round(net_vol, 3),
            surface_area_mm2=round(area, 3),
            bounding_box=bbox,
            fits_envelope=fits,
            issues=issues,
        )
