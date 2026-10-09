"""In-RAM Knowledge Graph & Cross-Document Citation Graph Engine for Privreach OS.

Features:
1. Multi-Modal Knowledge Network:
   - DOCUMENT nodes (PDF textbooks, audio files, video lectures)
   - CHUNK nodes (Prose, Formulas, Tables, Figures)
   - ENTITY nodes (Scientific eponyms, physical laws, constants)
2. Cross-Document Citation & Entity Bridging:
   - Detects entities shared across multiple documents.
   - Computes multi-document connective bridges.
3. Thematic Community Detection:
   - Greedy modularity community clustering on the entity semantic network.
4. Multi-Hop GraphRAG Retrieval Expansion:
   - Subgraph extraction for query context.
   - Personalized graph traversal augmenting vector/lexical retrieval.
5. In-Memory Persistence:
   - Zero-latency JSON serialization to RAM and disk cache.
"""

import os
import json
import time
from typing import List, Dict, Any, Optional, Set, Tuple

import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities

from privearch.schemas import (
    DocumentChunk,
    ScoredChunk,
    GraphNode,
    GraphEdge,
    GraphNodeType,
    GraphEdgeType,
    CrossDocumentBridge,
    GraphCommunity,
    GraphSubnetwork
)
from privearch.graph.entity_extractor import ScientificEntityExtractor, ExtractedRelation


class KnowledgeGraphEngine:
    """
    In-RAM Graph Engine powering Privreach GraphRAG and Cross-Document Citations.
    """

    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.communities: List[GraphCommunity] = []
        self.bridges: List[CrossDocumentBridge] = []
        self._dirty = False
        self._last_community_update = 0.0

    def clear(self):
        """Reset the knowledge graph."""
        self.graph.clear()
        self.communities.clear()
        self.bridges.clear()
        self._dirty = True

    def index_chunk(self, chunk: DocumentChunk):
        """
        Ingests a single document chunk into the knowledge graph:
        1. Document node & CONTAINS edge
        2. Chunk node
        3. Entities extracted & MENTIONS edges
        4. Co-occurring semantic relation edges
        5. Bibliographic citation edges
        """
        doc_node_id = f"doc:{chunk.doc_name}"
        chunk_node_id = f"chunk:{chunk.chunk_id}"

        # 1. Document Node
        if not self.graph.has_node(doc_node_id):
            self.graph.add_node(
                doc_node_id,
                label=chunk.doc_name,
                node_type=GraphNodeType.DOCUMENT.value,
                doc_name=chunk.doc_name,
                page_num=None,
                degree=0,
                community_id=0
            )

        # 2. Chunk Node
        ev_type = getattr(chunk, "evidence_type", "DOCUMENT_PAGE")
        self.graph.add_node(
            chunk_node_id,
            label=f"{chunk.doc_name} (p.{chunk.page_num})",
            node_type=GraphNodeType.CHUNK.value,
            doc_name=chunk.doc_name,
            page_num=chunk.page_num,
            evidence_type=ev_type,
            section=chunk.section_header or "",
            degree=0,
            community_id=0
        )

        # Edge: Document -> Chunk
        self.graph.add_edge(
            doc_node_id,
            chunk_node_id,
            key=GraphEdgeType.CONTAINS.value,
            relation=GraphEdgeType.CONTAINS.value,
            weight=1.0,
            is_cross_document=False
        )

        # 3. Extract Entities
        entities = ScientificEntityExtractor.extract_entities(chunk.text)
        for ent in entities:
            ent_node_id = f"ent:{ent}"
            if not self.graph.has_node(ent_node_id):
                self.graph.add_node(
                    ent_node_id,
                    label=ent,
                    node_type=GraphNodeType.ENTITY.value,
                    doc_name=chunk.doc_name,
                    page_num=chunk.page_num,
                    degree=0,
                    community_id=0
                )

            # Edge: Chunk -> Entity
            edge_type = GraphEdgeType.DEFINES.value if ev_type == "MATHEMATICAL_FORMULA" else GraphEdgeType.MENTIONS.value
            self.graph.add_edge(
                chunk_node_id,
                ent_node_id,
                key=edge_type,
                relation=edge_type,
                weight=1.5 if edge_type == GraphEdgeType.DEFINES.value else 1.0,
                is_cross_document=False
            )

        # 4. Extract Relations between Co-occurring Entities
        relations = ScientificEntityExtractor.extract_relations(chunk.text, entities=entities)
        for rel in relations:
            src_id = f"ent:{rel.subject}"
            tgt_id = f"ent:{rel.obj}"
            if self.graph.has_node(src_id) and self.graph.has_node(tgt_id):
                self.graph.add_edge(
                    src_id,
                    tgt_id,
                    key=f"rel:{rel.predicate}",
                    relation=rel.predicate,
                    weight=rel.weight,
                    evidence=rel.evidence,
                    is_cross_document=False
                )

        # 5. Extract Citations
        citations = ScientificEntityExtractor.extract_citations(chunk.text)
        for cit in citations:
            cit_node_id = f"cit:{cit}"
            if not self.graph.has_node(cit_node_id):
                self.graph.add_node(
                    cit_node_id,
                    label=cit,
                    node_type=GraphNodeType.ENTITY.value,
                    doc_name=chunk.doc_name,
                    page_num=chunk.page_num,
                    degree=0,
                    community_id=0
                )
            self.graph.add_edge(
                chunk_node_id,
                cit_node_id,
                key=GraphEdgeType.CITES.value,
                relation=GraphEdgeType.CITES.value,
                weight=1.0,
                is_cross_document=False
            )

        self._dirty = True

    def index_chunks(self, chunks: List[DocumentChunk]):
        """Batch index chunks and refresh graph analytics."""
        t0 = time.time()
        for chunk in chunks:
            self.index_chunk(chunk)
        self.detect_cross_document_bridges()
        self.detect_communities()
        self._dirty = False

    def detect_cross_document_bridges(self) -> List[CrossDocumentBridge]:
        """
        Identifies entities that are referenced across 2 or more distinct documents.
        These entities serve as multi-document reasoning hubs.
        """
        bridges: List[CrossDocumentBridge] = []
        entity_nodes = [n for n, d in self.graph.nodes(data=True) if d.get("node_type") == GraphNodeType.ENTITY.value]

        for ent_id in entity_nodes:
            label = self.graph.nodes[ent_id].get("label", ent_id)
            # Find incoming chunk nodes
            predecessors = list(self.graph.predecessors(ent_id))
            chunk_nodes = [p for p in predecessors if p.startswith("chunk:")]
            
            docs: Set[str] = set()
            chunk_ids: List[str] = []
            for c_id in chunk_nodes:
                doc = self.graph.nodes[c_id].get("doc_name")
                if doc:
                    docs.add(doc)
                    chunk_ids.append(c_id.replace("chunk:", ""))

            if len(docs) >= 2:
                # Find outgoing semantic relations
                relations: Set[str] = set()
                for _, tgt, data in self.graph.out_edges(ent_id, data=True):
                    rel = data.get("relation", "")
                    if rel:
                        relations.add(rel)

                bridge = CrossDocumentBridge(
                    entity=label,
                    documents=sorted(list(docs)),
                    chunk_ids=chunk_ids,
                    shared_relations=sorted(list(relations))
                )
                bridges.append(bridge)

        self.bridges = sorted(bridges, key=lambda b: len(b.documents), reverse=True)
        return self.bridges

    def detect_communities(self) -> List[GraphCommunity]:
        """
        Detects thematic knowledge clusters using modularity optimization
        on the undirected projection of the entity co-occurrence sub-network.
        """
        # Build undirected entity co-occurrence projection
        entity_nodes = [n for n, d in self.graph.nodes(data=True) if d.get("node_type") == GraphNodeType.ENTITY.value]
        if len(entity_nodes) < 3:
            self.communities = []
            return []

        ent_subgraph = nx.Graph()
        for ent_id in entity_nodes:
            ent_subgraph.add_node(ent_id, label=self.graph.nodes[ent_id].get("label", ent_id))

        # Add edges between entities connected by relations or shared chunks
        for ent_id in entity_nodes:
            # direct relations
            for _, tgt in self.graph.out_edges(ent_id):
                if tgt in entity_nodes and ent_id != tgt:
                    ent_subgraph.add_edge(ent_id, tgt)
            # chunks mentioning both
            preds = [p for p in self.graph.predecessors(ent_id) if p.startswith("chunk:")]
            for chunk_id in preds[:10]:
                for succ in self.graph.successors(chunk_id):
                    if succ in entity_nodes and succ != ent_id:
                        ent_subgraph.add_edge(ent_id, succ)

        if ent_subgraph.number_of_edges() == 0:
            self.communities = []
            return []

        try:
            raw_communities = list(greedy_modularity_communities(ent_subgraph))
        except Exception:
            self.communities = []
            return []

        communities: List[GraphCommunity] = []
        for idx, comm in enumerate(raw_communities, start=1):
            members = [ent_subgraph.nodes[n].get("label", n) for n in comm]
            # Degree centrality within community
            sub = ent_subgraph.subgraph(comm)
            degrees = sorted(sub.degree(), key=lambda x: x[1], reverse=True)
            top_entities = [ent_subgraph.nodes[n].get("label", n) for n, _ in degrees[:3]]

            # Update community_id on graph nodes
            for n in comm:
                if self.graph.has_node(n):
                    self.graph.nodes[n]["community_id"] = idx

            title = " & ".join(top_entities[:2]) + " Domain" if top_entities else f"Thematic Cluster {idx}"
            summary = f"Cluster of {len(members)} interconnected scientific concepts centered around {', '.join(top_entities)}."

            communities.append(GraphCommunity(
                community_id=idx,
                title=title,
                summary=summary,
                members=members[:15],
                central_nodes=top_entities
            ))

        self.communities = communities
        return self.communities

    def query_subgraph(
        self,
        query: str,
        top_k_entities: int = 6,
        depth: int = 2
    ) -> GraphSubnetwork:
        """
        Extracts a localized subnetwork tailored to the user query:
        1. Identifies seed entity nodes matching query terms.
        2. Traverses BFS neighbor subgraph (depth 1-2).
        3. Identifies cross-document bridges and thematic communities in context.
        """
        if self._dirty:
            self.detect_cross_document_bridges()
            self.detect_communities()
            self._dirty = False

        query_entities = ScientificEntityExtractor.extract_entities(query)
        query_lower = query.lower()

        # Match entity nodes
        matched_node_ids: Set[str] = set()
        for n, d in self.graph.nodes(data=True):
            if d.get("node_type") == GraphNodeType.ENTITY.value:
                lbl = d.get("label", "").lower()
                if lbl in query_lower or any(qe.lower() in lbl for qe in query_entities):
                    matched_node_ids.add(n)

        # Fallback: if no direct match, take top-degree entities
        if not matched_node_ids:
            ent_degrees = [
                (n, self.graph.degree(n))
                for n, d in self.graph.nodes(data=True)
                if d.get("node_type") == GraphNodeType.ENTITY.value
            ]
            ent_degrees.sort(key=lambda x: x[1], reverse=True)
            matched_node_ids = {n for n, _ in ent_degrees[:top_k_entities]}

        # Subgraph BFS expansion
        visited_nodes: Set[str] = set(matched_node_ids)
        frontier: Set[str] = set(matched_node_ids)

        for _ in range(depth):
            next_frontier: Set[str] = set()
            for u in frontier:
                for v in self.graph.successors(u):
                    if v not in visited_nodes:
                        next_frontier.add(v)
                        visited_nodes.add(v)
                for v in self.graph.predecessors(u):
                    if v not in visited_nodes:
                        next_frontier.add(v)
                        visited_nodes.add(v)
            frontier = next_frontier
            if len(visited_nodes) >= 60:
                break

        # Convert to GraphNode and GraphEdge models
        sub_nodes: List[GraphNode] = []
        for n in visited_nodes:
            d = self.graph.nodes[n]
            sub_nodes.append(GraphNode(
                id=n,
                label=d.get("label", n),
                type=GraphNodeType(d.get("node_type", GraphNodeType.ENTITY.value)),
                doc_name=d.get("doc_name"),
                page_num=d.get("page_num"),
                degree=self.graph.degree(n),
                community_id=d.get("community_id", 0)
            ))

        sub_edges: List[GraphEdge] = []
        for u, v, data in self.graph.edges(visited_nodes, data=True):
            if u in visited_nodes and v in visited_nodes:
                rel = data.get("relation", GraphEdgeType.RELATES_TO.value)
                # Map to enum or default
                try:
                    rel_enum = GraphEdgeType(rel)
                except ValueError:
                    rel_enum = GraphEdgeType.RELATES_TO

                sub_edges.append(GraphEdge(
                    source=u,
                    target=v,
                    relation=rel_enum,
                    weight=data.get("weight", 1.0),
                    is_cross_document=data.get("is_cross_document", False)
                ))

        # Relevant bridges
        sub_ent_labels = {d.get("label") for n, d in self.graph.nodes(data=True) if n in visited_nodes}
        relevant_bridges = [b for b in self.bridges if b.entity in sub_ent_labels]

        # Relevant communities
        relevant_comm_ids = {d.get("community_id", 0) for n, d in self.graph.nodes(data=True) if n in visited_nodes}
        relevant_communities = [c for c in self.communities if c.community_id in relevant_comm_ids]

        return GraphSubnetwork(
            nodes=sub_nodes,
            edges=sub_edges,
            bridges=relevant_bridges,
            communities=relevant_communities,
            total_nodes=len(sub_nodes),
            total_edges=len(sub_edges)
        )

    def expand_retrieval(
        self,
        query: str,
        retrieved_chunks: List[ScoredChunk],
        all_chunks: List[DocumentChunk],
        max_expansion: int = 3
    ) -> List[DocumentChunk]:
        """
        Multi-hop GraphRAG Retrieval Expansion:
        Traverses entity hubs and cross-document bridges to identify high-centrality
        neighbor chunks connected to retrieved evidence that standard lexical/vector search missed.
        """
        if not retrieved_chunks or not all_chunks:
            return []

        chunk_map = {c.chunk_id: c for c in all_chunks}
        retrieved_ids = {sc.chunk.chunk_id for sc in retrieved_chunks}

        candidate_chunk_scores: Dict[str, float] = {}

        for sc in retrieved_chunks:
            c_node = f"chunk:{sc.chunk.chunk_id}"
            if not self.graph.has_node(c_node):
                continue

            # Entities mentioned in this retrieved chunk
            for _, ent_node, data in self.graph.out_edges(c_node, data=True):
                if not ent_node.startswith("ent:"):
                    continue

                # Find sibling chunks connected to this same entity
                for sibling_chunk, _, _ in self.graph.in_edges(ent_node, data=True):
                    if not sibling_chunk.startswith("chunk:"):
                        continue
                    sib_id = sibling_chunk.replace("chunk:", "")
                    if sib_id not in retrieved_ids and sib_id in chunk_map:
                        # Weight cross-document bridges higher
                        is_bridge = any(b.entity == self.graph.nodes[ent_node].get("label") for b in self.bridges)
                        boost = 2.0 if is_bridge else 1.0
                        candidate_chunk_scores[sib_id] = candidate_chunk_scores.get(sib_id, 0.0) + (sc.rrf_score * boost)

        # Sort candidate chunks
        sorted_candidates = sorted(candidate_chunk_scores.items(), key=lambda x: x[1], reverse=True)
        expanded: List[DocumentChunk] = []
        for cid, _ in sorted_candidates[:max_expansion]:
            if cid in chunk_map:
                expanded.append(chunk_map[cid])

        return expanded

    def export_json(self) -> Dict[str, Any]:
        """Serialize knowledge graph state to JSON-serializable dictionary."""
        nodes_list = []
        for n, d in self.graph.nodes(data=True):
            nodes_list.append({
                "id": n,
                "label": d.get("label", n),
                "node_type": d.get("node_type", "ENTITY"),
                "doc_name": d.get("doc_name"),
                "page_num": d.get("page_num"),
                "degree": self.graph.degree(n),
                "community_id": d.get("community_id", 0)
            })

        edges_list = []
        for u, v, data in self.graph.edges(data=True):
            edges_list.append({
                "source": u,
                "target": v,
                "relation": data.get("relation", "RELATES_TO"),
                "weight": data.get("weight", 1.0),
                "is_cross_document": data.get("is_cross_document", False)
            })

        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "nodes": nodes_list,
            "edges": edges_list,
            "bridges": [b.model_dump() for b in self.bridges],
            "communities": [c.model_dump() for c in self.communities]
        }

    def import_json(self, data: Dict[str, Any]):
        """Deserialize knowledge graph state from dictionary."""
        self.clear()
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])

        for n in nodes:
            self.graph.add_node(
                n["id"],
                label=n.get("label", n["id"]),
                node_type=n.get("node_type", "ENTITY"),
                doc_name=n.get("doc_name"),
                page_num=n.get("page_num"),
                degree=n.get("degree", 0),
                community_id=n.get("community_id", 0)
            )

        for e in edges:
            self.graph.add_edge(
                e["source"],
                e["target"],
                key=e.get("relation", "RELATES_TO"),
                relation=e.get("relation", "RELATES_TO"),
                weight=e.get("weight", 1.0),
                is_cross_document=e.get("is_cross_document", False)
            )

        self.bridges = [CrossDocumentBridge(**b) for b in data.get("bridges", [])]
        self.communities = [GraphCommunity(**c) for c in data.get("communities", [])]
        self._dirty = False

    def save_to_dir(self, target_dir: str) -> bool:
        """Persist graph structure to target directory as graph.json."""
        try:
            os.makedirs(target_dir, exist_ok=True)
            path = os.path.join(target_dir, "graph.json")
            data = self.export_json()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[Warning] Failed to save graph index: {e}")
            return False

    def load_from_dir(self, target_dir: str) -> bool:
        """Load graph structure from graph.json if present."""
        path = os.path.join(target_dir, "graph.json")
        if not os.path.exists(path):
            return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.import_json(data)
            return True
        except Exception as e:
            print(f"[Warning] Failed to load graph index: {e}")
            return False
