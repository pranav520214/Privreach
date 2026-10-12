"""
privreach.cad: Generative Parametric Code-CAD, PCB & FEA Simulation Subsystem.

Responsible for:
- Generative CadQuery Python script synthesis (BREP geometry via OpenCASCADE)
- Geometry validation (manifold checks, bounding boxes, volume validation)
- Finite Element Analysis (FEA) for von Mises stress, deflection, and safety factors
- Bionic design patterns (TPMS gyroids, Voronoi lattices, cellular infill)
- Programmatic PCB layout script generation and DRC checking
"""

from privreach.cad.cadquery_generator import CadQueryGenerator, CadScriptResult
from privreach.cad.sandbox_executor import SandboxCADExecutor, GeometryValidationResult
from privreach.cad.fea_runner import FEARunner, FEAResult, MaterialProperties
from privreach.cad.bionic.pattern_library import BionicPatternLibrary, BionicPatternResult
from privreach.cad.pcb.kicad_generator import KiCadGenerator, PCBScriptResult

__all__ = [
    "CadQueryGenerator",
    "CadScriptResult",
    "SandboxCADExecutor",
    "GeometryValidationResult",
    "FEARunner",
    "FEAResult",
    "MaterialProperties",
    "BionicPatternLibrary",
    "BionicPatternResult",
    "KiCadGenerator",
    "PCBScriptResult",
]
