"""
Swanson ABC Literature-Based Discovery Engine.

Uncovers undiscovered public scientific knowledge using the Swanson ABC paradigm:
- Open Discovery (A -> B -> ?): Find hidden connections C linked via intermediate B terms
  that have never directly co-occurred with A in any publication.
- Closed Discovery (A -> ? -> C): Given two disjoint entities A and C, identify the
  intermediate bridging mechanisms B that explain their latent connection.
"""

from typing import List, Dict, Set, Tuple, Optional, Any
import math
from collections import defaultdict
import networkx as nx
from pydantic import BaseModel, Field


class DiscoveryCandidate(BaseModel):
    """A discovered entity C hypothesized to have a hidden connection with A."""
    target_entity: str
    discovery_score: float
    bridging_mechanisms: List[str] = Field(default_factory=list)
    path_count: int = 0
    confidence_tier: str = "HIGH"  # HIGH, MEDIUM, EXPLORATORY
    rationale: str = ""


class SwansonDiscoveryReport(BaseModel):
    """Structured report containing validated hypothesis discoveries."""
    mode: str  # "open_discovery" or "closed_discovery"
    source_entity: str
    target_entity: Optional[str] = None
    total_triads_evaluated: int = 0
    candidates: List[DiscoveryCandidate] = Field(default_factory=list)
    bridges_found: List[str] = Field(default_factory=list)


class SwansonDiscoveryEngine:
    """
    Executes graph-theoretic ABC literature-based discovery.
    Operates on NetworkX knowledge graphs constructed from vault literature.
    """

    def __init__(self, graph: Optional[nx.Graph] = None):
        self.graph = graph if graph is not None else nx.MultiDiGraph()

    def set_graph(self, graph: nx.Graph) -> None:
        """Updates internal graph reference."""
        self.graph = graph

    def _normalize_name(self, name: str) -> str:
        """Normalizes entity names for robust graph lookup."""
        return name.strip().lower()

    def _get_neighbors(self, node: str) -> Set[str]:
        """Returns undirected union of successors and predecessors in the graph."""
        if not self.graph.has_node(node):
            # Attempt case-insensitive lookup
            matched_node = None
            norm = self._normalize_name(node)
            for n in self.graph.nodes():
                if self._normalize_name(str(n)) == norm:
                    matched_node = n
                    break
            if not matched_node:
                return set()
            node = matched_node

        neighbors: Set[str] = set()
        if self.graph.is_directed():
            neighbors.update(self.graph.successors(node))
            neighbors.update(self.graph.predecessors(node))
        else:
            neighbors.update(self.graph.neighbors(node))
        return neighbors

    def _get_edge_weight(self, u: str, v: str) -> float:
        """Retrieves edge weight or co-occurrence count between u and v."""
        if not self.graph.has_edge(u, v):
            if self.graph.is_directed() and self.graph.has_edge(v, u):
                return self._get_edge_weight(v, u)
            return 1.0

        edge_data = self.graph.get_edge_data(u, v)
        if isinstance(edge_data, dict):
            # Handle MultiGraph structure
            if 0 in edge_data and isinstance(edge_data[0], dict):
                return float(edge_data[0].get("weight", 1.0))
            return float(edge_data.get("weight", 1.0))
        return 1.0

    def open_discovery(
        self,
        entity_a: str,
        top_k: int = 15,
        min_bridges: int = 1,
    ) -> SwansonDiscoveryReport:
        """
        Executes Open Discovery (A -> B -> ?):
        Finds all candidate entities C connected through intermediates B that have
        NEVER been directly linked with entity A.
        """
        norm_a = self._normalize_name(entity_a)
        canonical_a = None
        for n in self.graph.nodes():
            if self._normalize_name(str(n)) == norm_a:
                canonical_a = n
                break

        if canonical_a is None:
            return SwansonDiscoveryReport(
                mode="open_discovery",
                source_entity=entity_a,
                total_triads_evaluated=0,
                candidates=[],
                bridges_found=[],
            )

        # 1. Identify all direct 1-hop neighbors of A: {B}
        b_neighbors = self._get_neighbors(canonical_a)
        if not b_neighbors:
            return SwansonDiscoveryReport(
                mode="open_discovery",
                source_entity=entity_a,
                total_triads_evaluated=0,
                candidates=[],
                bridges_found=[],
            )

        # 2. Collect all 2-hop candidate neighbors {C} connected through {B}
        # c_bridges: mapping C -> list of bridging B nodes
        c_bridges: Dict[str, List[str]] = defaultdict(list)
        triads_count = 0

        for b in b_neighbors:
            # Get neighbors of intermediate node B
            c_neighbors = self._get_neighbors(b)
            for c in c_neighbors:
                triads_count += 1
                # Filter out A itself
                if c == canonical_a:
                    continue
                # Filter out entities that are ALREADY direct neighbors of A
                # (These are already-known connections, not novel discoveries)
                if c in b_neighbors:
                    continue

                c_bridges[c].append(b)

        # 3. Score candidate C entities using path strength and bridge centrality
        candidates: List[DiscoveryCandidate] = []
        for c, bridges in c_bridges.items():
            if len(bridges) < min_bridges:
                continue

            # Path-based Swanson score
            score = 0.0
            for b in bridges:
                w_ab = self._get_edge_weight(canonical_a, b)
                w_bc = self._get_edge_weight(b, c)
                b_degree = len(self._get_neighbors(b))
                # Penalize overly generic hub terms (e.g. "cell", "protein", "system")
                hub_penalty = math.log10(b_degree + 10)
                score += (w_ab * w_bc) / max(1.0, hub_penalty)

            # Normalization factor by unique bridge diversity
            bridge_multiplier = math.sqrt(len(bridges))
            final_score = round(score * bridge_multiplier, 4)

            # Confidence classification
            tier = "HIGH" if len(bridges) >= 3 else ("MEDIUM" if len(bridges) >= 2 else "EXPLORATORY")

            rationale = (
                f"Hypothesized link between '{canonical_a}' and '{c}' supported by "
                f"{len(bridges)} independent bridging mechanisms: {', '.join(bridges[:4])}"
            )

            candidates.append(
                DiscoveryCandidate(
                    target_entity=str(c),
                    discovery_score=final_score,
                    bridging_mechanisms=[str(b) for b in bridges],
                    path_count=len(bridges),
                    confidence_tier=tier,
                    rationale=rationale,
                )
            )

        candidates.sort(key=lambda x: x.discovery_score, reverse=True)

        return SwansonDiscoveryReport(
            mode="open_discovery",
            source_entity=str(canonical_a),
            total_triads_evaluated=triads_count,
            candidates=candidates[:top_k],
            bridges_found=list(b_neighbors),
        )

    def closed_discovery(
        self,
        entity_a: str,
        entity_c: str,
    ) -> SwansonDiscoveryReport:
        """
        Executes Closed Discovery (A -> ? -> C):
        Finds and ranks all intermediate bridging mechanisms {B} explaining the latent
        connection between two disjoint target entities A and C.
        """
        canonical_a = None
        canonical_c = None
        norm_a = self._normalize_name(entity_a)
        norm_c = self._normalize_name(entity_c)

        for n in self.graph.nodes():
            if self._normalize_name(str(n)) == norm_a:
                canonical_a = n
            if self._normalize_name(str(n)) == norm_c:
                canonical_c = n

        if canonical_a is None or canonical_c is None:
            return SwansonDiscoveryReport(
                mode="closed_discovery",
                source_entity=entity_a,
                target_entity=entity_c,
                total_triads_evaluated=0,
                candidates=[],
                bridges_found=[],
            )

        # Direct connection check
        is_directly_connected = canonical_c in self._get_neighbors(canonical_a)

        # Intermediate bridges: neighbors of A intersection neighbors of C
        a_neighbors = self._get_neighbors(canonical_a)
        c_neighbors = self._get_neighbors(canonical_c)
        shared_bridges = a_neighbors.intersection(c_neighbors)

        ranked_bridges: List[DiscoveryCandidate] = []
        for b in shared_bridges:
            w_ab = self._get_edge_weight(canonical_a, b)
            w_bc = self._get_edge_weight(b, canonical_c)
            b_degree = len(self._get_neighbors(b))
            score = round((w_ab * w_bc) / math.log10(b_degree + 10), 4)

            ranked_bridges.append(
                DiscoveryCandidate(
                    target_entity=str(b),
                    discovery_score=score,
                    bridging_mechanisms=[str(b)],
                    path_count=1,
                    confidence_tier="HIGH",
                    rationale=f"Bridge '{b}' links '{canonical_a}' and '{canonical_c}'",
                )
            )

        ranked_bridges.sort(key=lambda x: x.discovery_score, reverse=True)

        return SwansonDiscoveryReport(
            mode="closed_discovery",
            source_entity=str(canonical_a),
            target_entity=str(canonical_c),
            total_triads_evaluated=len(a_neighbors) * len(c_neighbors),
            candidates=ranked_bridges,
            bridges_found=[str(b) for b in shared_bridges],
        )
