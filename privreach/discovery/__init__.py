"""
privreach.discovery: Hidden Pattern and Literature-Based Discovery Subsystem.

Responsible for:
- Swanson ABC literature discovery (Open A -> B -> ? and Closed A -> ? -> C)
- SymPy Abstract Syntax Tree (AST) canonical equation isomorphism detection
- Knowledge graph community clustering and boundary-spanning bridge entity detection
- Deterministic logical proposition contradiction detection using SymPy SAT/Z3
"""

from privreach.discovery.swanson_abc import SwansonDiscoveryEngine, DiscoveryCandidate, SwansonDiscoveryReport
from privreach.discovery.equation_isomorphism import EquationIsomorphismEngine, IsomorphismCluster, EquationNode
from privreach.discovery.community_detector import GraphCommunityDetector, CommunityReport, BridgeEntity
from privreach.discovery.contradiction_finder import ContradictionFinder, ContradictionRecord, ContradictionReport

__all__ = [
    "SwansonDiscoveryEngine",
    "DiscoveryCandidate",
    "SwansonDiscoveryReport",
    "EquationIsomorphismEngine",
    "IsomorphismCluster",
    "EquationNode",
    "GraphCommunityDetector",
    "CommunityReport",
    "BridgeEntity",
    "ContradictionFinder",
    "ContradictionRecord",
    "ContradictionReport",
]
