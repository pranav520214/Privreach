"""
Unit and Integration Tests for privreach.discovery subsystem.
"""

import unittest
import networkx as nx

from privreach.discovery.swanson_abc import SwansonDiscoveryEngine
from privreach.discovery.equation_isomorphism import EquationIsomorphismEngine
from privreach.discovery.community_detector import GraphCommunityDetector
from privreach.discovery.contradiction_finder import ContradictionFinder


class TestDiscoverySubsystem(unittest.TestCase):
    """Verifies hidden pattern discovery, isomorphism detection, and contradiction finding."""

    def setUp(self):
        # 1. Setup Knowledge Graph for Swanson ABC Testing
        self.graph = nx.Graph()
        # Classic Swanson test case: Raynaud's Syndrome <-> Blood Viscosity <-> Dietary Fish Oil
        self.graph.add_edge("raynaud syndrome", "blood viscosity", weight=5.0)
        self.graph.add_edge("blood viscosity", "dietary fish oil", weight=4.0)
        self.graph.add_edge("blood viscosity", "platelet aggregation", weight=3.0)
        self.graph.add_edge("platelet aggregation", "dietary fish oil", weight=2.0)
        self.graph.add_edge("raynaud syndrome", "cold sensitivity", weight=6.0)

        self.swanson_engine = SwansonDiscoveryEngine(self.graph)
        self.isomorphism_engine = EquationIsomorphismEngine()
        self.community_detector = GraphCommunityDetector()
        self.contradiction_finder = ContradictionFinder()

    def test_swanson_open_discovery(self):
        """Discovers unlinked entity C through intermediate bridges B."""
        report = self.swanson_engine.open_discovery("raynaud syndrome", top_k=5)
        self.assertEqual(report.mode, "open_discovery")
        self.assertGreater(len(report.candidates), 0)

        # "dietary fish oil" must be discovered as a candidate
        candidate_names = [c.target_entity for c in report.candidates]
        self.assertIn("dietary fish oil", candidate_names)

        # The candidate must have "blood viscosity" in its bridging mechanisms
        fish_oil_cand = next(c for c in report.candidates if c.target_entity == "dietary fish oil")
        self.assertIn("blood viscosity", fish_oil_cand.bridging_mechanisms)
        self.assertGreater(fish_oil_cand.discovery_score, 0.0)

    def test_swanson_closed_discovery(self):
        """Identifies shared intermediate bridges B connecting two target concepts A and C."""
        report = self.swanson_engine.closed_discovery("raynaud syndrome", "dietary fish oil")
        self.assertEqual(report.mode, "closed_discovery")
        self.assertIn("blood viscosity", report.bridges_found)
        self.assertGreaterEqual(len(report.candidates), 1)

    def test_equation_ast_isomorphism_detection(self):
        """Identifies mathematical isomorphisms across disparate scientific domains."""
        # Newton's Gravitation (Astrophysics): F = G * m1 * m2 / r^2
        self.isomorphism_engine.register_equation(
            name="Newtonian Gravitation",
            expression_str="G * m1 * m2 / (r**2)",
            domain="astrophysics",
        )

        # Coulomb's Law (Electromagnetism): F = k * q1 * q2 / r^2
        self.isomorphism_engine.register_equation(
            name="Coulombs Law",
            expression_str="k * q1 * q2 / (r**2)",
            domain="electromagnetism",
        )

        # Hooke's Law (Mechanics - different structure): F = -k * x
        self.isomorphism_engine.register_equation(
            name="Hookes Law",
            expression_str="-k * x",
            domain="classical_mechanics",
        )

        report = self.isomorphism_engine.detect_isomorphisms()
        self.assertEqual(report.total_equations_indexed, 3)
        self.assertGreaterEqual(report.total_isomorphic_clusters, 1)

        # Verify cluster contains both gravitation and electrostatics
        cluster = report.cross_domain_discoveries[0]
        self.assertIn("astrophysics", cluster.domains_involved)
        self.assertIn("electromagnetism", cluster.domains_involved)
        eq_names = [eq.name for eq in cluster.equations]
        self.assertIn("Newtonian Gravitation", eq_names)
        self.assertIn("Coulombs Law", eq_names)

    def test_graph_community_detection_and_bridge_nodes(self):
        """Detects modular communities and isolates boundary-spanning bridge nodes."""
        # Build two dense clusters joined by a single bridge entity
        g = nx.Graph()
        # Cluster 1: Semiconductor Lithography
        cluster1 = ["euv", "duv", "photoresist", "stepper"]
        for i in range(len(cluster1)):
            for j in range(i + 1, len(cluster1)):
                g.add_edge(cluster1[i], cluster1[j], weight=2.0)

        # Cluster 2: Quantum Computing
        cluster2 = ["qubit", "surface code", "decoherence", "transmon"]
        for i in range(len(cluster2)):
            for j in range(i + 1, len(cluster2)):
                g.add_edge(cluster2[i], cluster2[j], weight=2.0)

        # Bridge node linking both domains: "nanofabrication"
        g.add_edge("nanofabrication", "photoresist", weight=3.0)
        g.add_edge("nanofabrication", "stepper", weight=3.0)
        g.add_edge("nanofabrication", "transmon", weight=3.0)
        g.add_edge("nanofabrication", "qubit", weight=3.0)

        report = self.community_detector.detect_communities(g)
        self.assertGreaterEqual(report.total_communities, 2)
        self.assertGreater(len(report.bridge_entities), 0)

        # "nanofabrication" must be identified as top bridge entity
        top_bridge = report.bridge_entities[0]
        self.assertEqual(top_bridge.entity_name, "nanofabrication")
        self.assertGreater(top_bridge.betweenness_centrality, 0.20)
        self.assertGreaterEqual(len(top_bridge.connected_communities), 2)

    def test_contradiction_polarity_opposition(self):
        """Detects polarity opposition contradiction (+1 vs -1) on identical subject-object."""
        self.contradiction_finder.add_claim(
            subject="pellicle",
            relation="improves",
            object="euv yield",
            source_doc="paper_alpha.pdf",
            page_num=3,
        )
        self.contradiction_finder.add_claim(
            subject="pellicle",
            relation="inhibits",
            object="euv yield",
            source_doc="paper_beta.pdf",
            page_num=7,
        )

        report = self.contradiction_finder.scan_all_contradictions()
        self.assertEqual(report.total_contradictions_found, 1)
        conf = report.contradictions[0]
        self.assertEqual(conf.contradiction_type, "POLARITY_OPPOSITION")
        self.assertFalse(conf.is_satisfiable)
        self.assertIn("paper_alpha.pdf", conf.explanation)
        self.assertIn("paper_beta.pdf", conf.explanation)

    def test_contradiction_disjoint_numeric_intervals(self):
        """Detects disjoint numeric measurement reports for same parameter."""
        self.contradiction_finder.add_claim(
            subject="hydride superconductor",
            relation="transition temperature",
            object="kelvin",
            source_doc="study_2023.pdf",
            numeric_range=(250.0, 260.0),
        )
        self.contradiction_finder.add_claim(
            subject="hydride superconductor",
            relation="transition temperature",
            object="kelvin",
            source_doc="study_2024.pdf",
            numeric_range=(180.0, 195.0),
        )

        report = self.contradiction_finder.scan_all_contradictions()
        self.assertEqual(report.total_contradictions_found, 1)
        conf = report.contradictions[0]
        self.assertEqual(conf.contradiction_type, "DISJOINT_INTERVAL")
        self.assertFalse(conf.is_satisfiable)


if __name__ == "__main__":
    unittest.main()
