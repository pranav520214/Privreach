"""
Knowledge Graph Community Detector and Bridge Entity Discovery.

Identifies densely connected research clusters and discovers 'boundary-spanning'
bridge entities that connect disparate scientific fields using modularity algorithms
and betweenness centrality metrics.
"""

from typing import List, Dict, Set, Tuple, Optional, Any
import networkx as nx
import networkx.algorithms.community as nx_comm
from pydantic import BaseModel, Field


class BridgeEntity(BaseModel):
    """An entity that spans across two or more distinct scientific communities."""
    entity_name: str
    betweenness_centrality: float
    connected_communities: List[int] = Field(default_factory=list)
    degree: int = 0
    interdisciplinary_role: str = ""


class CommunityCluster(BaseModel):
    """A thematic cluster of entities identified in the literature graph."""
    community_id: int
    size: int
    top_members: List[str] = Field(default_factory=list)
    dominant_relations: List[str] = Field(default_factory=list)


class CommunityReport(BaseModel):
    """Comprehensive analysis report of knowledge graph communities and bridge nodes."""
    total_nodes: int = 0
    total_communities: int = 0
    modularity: float = 0.0
    communities: List[CommunityCluster] = Field(default_factory=list)
    bridge_entities: List[BridgeEntity] = Field(default_factory=list)


class GraphCommunityDetector:
    """
    Decomposes knowledge graphs into modular subfields and identifies bridging concepts.
    """

    def __init__(self, min_community_size: int = 2):
        self.min_community_size = min_community_size

    def detect_communities(self, graph: nx.Graph) -> CommunityReport:
        """
        Partitions graph into modular communities and identifies boundary bridges.
        """
        if graph.number_of_nodes() < 2:
            return CommunityReport(
                total_nodes=graph.number_of_nodes(),
                total_communities=0,
                modularity=0.0,
                communities=[],
                bridge_entities=[],
            )

        # Convert to simple undirected graph for community detection
        if graph.is_directed() or graph.is_multigraph():
            simple_graph = nx.Graph()
            for u, v, data in graph.edges(data=True):
                if u != v:  # remove self-loops
                    w = float(data.get("weight", 1.0)) if isinstance(data, dict) else 1.0
                    if simple_graph.has_edge(u, v):
                        simple_graph[u][v]["weight"] += w
                    else:
                        simple_graph.add_edge(u, v, weight=w)
            for node in graph.nodes():
                if not simple_graph.has_node(node):
                    simple_graph.add_node(node)
        else:
            simple_graph = graph.copy()

        # Execute community partitioning (Louvain or Greedy Modularity fallback)
        try:
            communities_raw = nx_comm.louvain_communities(simple_graph, weight="weight", seed=42)
        except Exception:
            try:
                communities_raw = list(nx_comm.greedy_modularity_communities(simple_graph, weight="weight"))
            except Exception:
                communities_raw = [set(c) for c in nx.connected_components(simple_graph)]

        # Calculate modularity
        try:
            modularity_val = round(nx_comm.modularity(simple_graph, communities_raw, weight="weight"), 4)
        except Exception:
            modularity_val = 0.0

        # Node -> Community ID lookup
        node_to_comm: Dict[str, int] = {}
        community_clusters: List[CommunityCluster] = []

        for comm_idx, comm_set in enumerate(communities_raw):
            for node in comm_set:
                node_to_comm[str(node)] = comm_idx

            sorted_members = sorted(
                comm_set,
                key=lambda n: simple_graph.degree(n, weight="weight"),
                reverse=True,
            )

            community_clusters.append(
                CommunityCluster(
                    community_id=comm_idx,
                    size=len(comm_set),
                    top_members=[str(m) for m in sorted_members[:8]],
                    dominant_relations=[],
                )
            )

        # Calculate Betweenness Centrality to locate bridge nodes
        betweenness = nx.betweenness_centrality(simple_graph, weight="weight")

        bridge_entities: List[BridgeEntity] = []
        for node, bc_score in betweenness.items():
            # Check communities of neighbors
            neighbor_comms: Set[int] = set()
            for neighbor in simple_graph.neighbors(node):
                if str(neighbor) in node_to_comm:
                    neighbor_comms.add(node_to_comm[str(neighbor)])

            # An entity is a boundary-spanner if its connections cross 2 or more distinct communities
            if len(neighbor_comms) >= 2 and bc_score > 0.0:
                deg = simple_graph.degree(node)
                role = (
                    f"Bridge node linking {len(neighbor_comms)} distinct scientific subfields "
                    f"(Communities: {list(neighbor_comms)}) with betweenness centrality of {bc_score:.4f}."
                )

                bridge_entities.append(
                    BridgeEntity(
                        entity_name=str(node),
                        betweenness_centrality=round(bc_score, 4),
                        connected_communities=sorted(list(neighbor_comms)),
                        degree=deg,
                        interdisciplinary_role=role,
                    )
                )

        bridge_entities.sort(key=lambda b: b.betweenness_centrality, reverse=True)

        return CommunityReport(
            total_nodes=simple_graph.number_of_nodes(),
            total_communities=len(communities_raw),
            modularity=modularity_val,
            communities=community_clusters,
            bridge_entities=bridge_entities[:15],
        )
