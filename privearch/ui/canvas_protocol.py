"""Canvas Protocol: Data structures and message specifications for the Explainer Canvas."""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class CanvasViewType(str, Enum):
    PLOT_2D = "PLOT_2D"
    EQUATION_DERIVATION = "EQUATION_DERIVATION"
    PARTICLE_SIMULATION = "PARTICLE_SIMULATION"
    CLAIM_AUDIT_MAP = "CLAIM_AUDIT_MAP"
    EMPTY = "EMPTY"


class DerivationStep(BaseModel):
    step_number: int
    title: str
    latex: str
    explanation: str
    units_or_notes: str = ""


class CanvasPayload(BaseModel):
    """Full state bundle for the Explainer Canvas."""
    active_view: CanvasViewType = CanvasViewType.EMPTY
    title: str = "Explainer Canvas"
    subtitle: str = "Deterministic Scientific Workspace"
    equation_latex: str = ""
    derivation_steps: List[DerivationStep] = Field(default_factory=list)
    simulation_html: str = ""
    plotly_json: Optional[Dict[str, Any]] = None
    claims_summary: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = 0.0
