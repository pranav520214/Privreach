"""Unit & Integration Tests for Privreach GraphRAG & Cross-Document Citation Graph."""

import unittest
from privearch.schemas import DocumentChunk, ScoredChunk, GraphNodeType, GraphEdgeType
from privearch.graph.entity_extractor import ScientificEntityExtractor, ExtractedRelation
from privearch.graph.graph_engine import KnowledgeGraphEngine
from privearch.ui.canvas_generator import CanvasGenerator


class TestGraphRAG(unittest.TestCase):
    """Test suite verifying scientific entity extraction, cross-document citation graph, and GraphRAG."""

    def setUp(self):
        self.engine = KnowledgeGraphEngine()

    def test_entity_extraction_scientific_eponyms(self):
        """Test extracting normalized scientific entities and eponymous laws."""
        text = (
            "According to de Broglie's hypothesis, the de Broglie wavelength is lambda = h / p. "
            "This directly validates Bohr's model of atomic orbits and Planck's quantum theory."
        )
        entities = ScientificEntityExtractor.extract_entities(text)
        self.assertIn("de Broglie Wavelength", entities)
        self.assertIn("Bohr's Atomic Model", entities)
        self.assertIn("Planck's Quantum Theory", entities)

    def test_citation_extraction(self):
        """Test extracting academic citation brackets and author-year markers."""
        text = "As shown in [1] and [2], atomic spectra confirm quantization. See also Bohr (1913)."
        citations = ScientificEntityExtractor.extract_citations(text)
        self.assertIn("[1]", citations)
        self.assertIn("[2]", citations)
        self.assertIn("Bohr (1913)", citations)

    def test_semantic_relation_extraction(self):
        """Test extracting relational triplets between co-occurring scientific entities."""
        text = "The de Broglie wavelength is derived from Planck's constant and relates to Bohr's model."
        relations = ScientificEntityExtractor.extract_relations(text)
        self.assertTrue(len(relations) >= 1)
        # Check predicate categorization
        predicates = [r.predicate for r in relations]
        self.assertTrue(any(p in ("DERIVED_FROM", "RELATES_TO", "CO_OCCURS_WITH") for p in predicates))

    def test_cross_document_bridge_detection(self):
        """Test detecting entities shared between two distinct documents as cross-document bridges."""
        chunk_doc_a = DocumentChunk(
            chunk_id="chunk_a1",
            doc_name="Quantum_Mechanics_Vol1.pdf",
            page_num=14,
            text="The de Broglie wavelength formula lambda = h/p establishes matter waves for electrons."
        )
        chunk_doc_b = DocumentChunk(
            chunk_id="chunk_b1",
            doc_name="Atomic_Spectra_Vol2.pdf",
            page_num=28,
            text="Bohr orbit quantization requires that standing waves of the de Broglie wavelength fit the orbit."
        )
        self.engine.index_chunks([chunk_doc_a, chunk_doc_b])

        bridges = self.engine.detect_cross_document_bridges()
        self.assertTrue(len(bridges) >= 1)
        
        # Verify de Broglie Wavelength is a bridge
        bridge_entities = [b.entity for b in bridges]
        self.assertIn("de Broglie Wavelength", bridge_entities)

        target_bridge = next(b for b in bridges if b.entity == "de Broglie Wavelength")
        self.assertIn("Quantum_Mechanics_Vol1.pdf", target_bridge.documents)
        self.assertIn("Atomic_Spectra_Vol2.pdf", target_bridge.documents)
        self.assertIn("chunk_a1", target_bridge.chunk_ids)
        self.assertIn("chunk_b1", target_bridge.chunk_ids)

    def test_thematic_community_detection(self):
        """Test modularity-based community clustering on knowledge graph nodes."""
        chunks = [
            DocumentChunk(
                chunk_id="c1",
                doc_name="Physics.pdf",
                page_num=1,
                text="The de Broglie wavelength relates to matter waves and standing waves."
            ),
            DocumentChunk(
                chunk_id="c2",
                doc_name="Physics.pdf",
                page_num=2,
                text="Bohr radius and angular momentum quantize the energy levels."
            ),
            DocumentChunk(
                chunk_id="c3",
                doc_name="Physics.pdf",
                page_num=3,
                text="Planck's constant explains the photoelectric effect and Compton effect."
            )
        ]
        self.engine.index_chunks(chunks)
        communities = self.engine.detect_communities()
        self.assertTrue(len(communities) >= 1)
        for comm in communities:
            self.assertTrue(len(comm.members) > 0)
            self.assertTrue(len(comm.title) > 0)

    def test_query_subgraph_extraction(self):
        """Test extracting a localized subnetwork matching a query."""
        chunks = [
            DocumentChunk(
                chunk_id="c1",
                doc_name="DocA.pdf",
                page_num=5,
                text="de Broglie wavelength applies to electrons."
            ),
            DocumentChunk(
                chunk_id="c2",
                doc_name="DocB.pdf",
                page_num=10,
                text="Bohr quantization condition relates to de Broglie wavelength."
            )
        ]
        self.engine.index_chunks(chunks)
        sub = self.engine.query_subgraph("What is the de Broglie wavelength in Bohr quantization?")

        self.assertTrue(sub.total_nodes > 0)
        self.assertTrue(sub.total_edges > 0)
        node_labels = [n.label for n in sub.nodes]
        self.assertIn("de Broglie Wavelength", node_labels)

    def test_graph_rag_retrieval_expansion(self):
        """Test multi-hop retrieval expansion across knowledge graph neighbor nodes."""
        c1 = DocumentChunk(chunk_id="c1", doc_name="A.pdf", page_num=1, text="de Broglie wavelength lambda = h/p.")
        c2 = DocumentChunk(chunk_id="c2", doc_name="B.pdf", page_num=2, text="de Broglie wavelength explains standing wave.")
        c3 = DocumentChunk(chunk_id="c3", doc_name="C.pdf", page_num=3, text="Classical thermodynamics of ideal gases.")
        
        all_chunks = [c1, c2, c3]
        self.engine.index_chunks(all_chunks)

        retrieved = [ScoredChunk(chunk=c1, rrf_score=0.03, final_rank=1)]
        expanded = self.engine.expand_retrieval("Explain de Broglie wavelength", retrieved, all_chunks, max_expansion=2)

        # c2 should be expanded because it shares the 'de Broglie Wavelength' entity with c1
        self.assertEqual(len(expanded), 1)
        self.assertEqual(expanded[0].chunk_id, "c2")

    def test_json_export_import(self):
        """Test serializing and deserializing knowledge graph."""
        c = DocumentChunk(chunk_id="c1", doc_name="Book.pdf", page_num=3, text="Planck's constant quantizes energy.")
        self.engine.index_chunks([c])

        data = self.engine.export_json()
        self.assertTrue(data["total_nodes"] > 0)
        self.assertTrue(data["total_edges"] > 0)

        new_engine = KnowledgeGraphEngine()
        new_engine.import_json(data)
        self.assertEqual(new_engine.graph.number_of_nodes(), self.engine.graph.number_of_nodes())
        self.assertEqual(new_engine.graph.number_of_edges(), self.engine.graph.number_of_edges())

    def test_canvas_graph_markdown_generation(self):
        """Test generating Explainer Canvas Markdown with Mermaid and Cross-Document Bridge tables."""
        c1 = DocumentChunk(chunk_id="c1", doc_name="Doc1.pdf", page_num=1, text="de Broglie wavelength matter waves.")
        c2 = DocumentChunk(chunk_id="c2", doc_name="Doc2.pdf", page_num=2, text="de Broglie wavelength in Bohr orbits.")
        self.engine.index_chunks([c1, c2])

        sub = self.engine.query_subgraph("de Broglie wavelength")
        md = CanvasGenerator.generate_graph_markdown(sub)

        self.assertIn("Knowledge Graph & Cross-Document Citation Network", md)
        self.assertIn("```mermaid", md)
        self.assertIn("graph LR", md)
        self.assertIn("Cross-Document Conceptual Bridges", md)
        self.assertIn("de Broglie Wavelength", md)


if __name__ == "__main__":
    unittest.main()
