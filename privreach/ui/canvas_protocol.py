"""Canvas Protocol: Data structures and message specifications for the Explainer Canvas."""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class CanvasViewType(str, Enum):
    PLOT_2D = "PLOT_2D"
    EQUATION_DERIVATION = "EQUATION_DERIVATION"
    PARTICLE_SIMULATION = "PARTICLE_SIMULATION"
    CLAIM_AUDIT_MAP = "CLAIM_AUDIT_MAP"
    MULTIMODAL_TIMELINE = "MULTIMODAL_TIMELINE"
    MEETING_MEMO = "MEETING_MEMO"
    VISUAL_FIGURE = "VISUAL_FIGURE"
    STRUCTURED_TABLE = "STRUCTURED_TABLE"
    REASONING_TRACE = "REASONING_TRACE"
    KNOWLEDGE_GRAPH = "KNOWLEDGE_GRAPH"
    CITATION_GRAPH = "CITATION_GRAPH"
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
    figure_path: Optional[str] = None
    figure_caption: str = ""
    table_markdown: str = ""
    reasoning_trace: Optional[str] = None
    reasoning_steps: List[Dict[str, Any]] = Field(default_factory=list)
    thinking_duration_s: float = 0.0
    graph_markdown: str = ""
    graph_subnetwork: Optional[Dict[str, Any]] = None
    timestamp: float = 0.0
