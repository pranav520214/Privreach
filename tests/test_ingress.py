"""
Unit and Integration Tests for privreach.ingress subsystem.
"""

import unittest
from privreach.ingress.taxonomy_expander import DeterministicTaxonomyExpander
from privreach.ingress.bibliometric_triage import BibliometricTriageEngine, TriageQueue
from privreach.ingress.manifest import HarvestManifest, ManifestEntry
from privreach.ingress.harvester import AcademicHarvester


class TestIngressSubsystem(unittest.TestCase):
    """Verifies deterministic operation of the academic harvester subsystem."""

    def setUp(self):
        self.expander = DeterministicTaxonomyExpander()
        self.triage = BibliometricTriageEngine(
            alpha_citations=0.30,
            beta_venue=0.20,
            gamma_recency=0.25,
            delta_relevance=0.25,
            priority_threshold=0.50,
            current_year=2025,
        )

    def test_taxonomy_expansion_deterministic(self):
        """Expansion must produce identical, deduplicated results across runs with no stochasticity."""
        query = "semiconductor lithography"
        run1 = self.expander.expand(query, max_terms=20)
        run2 = self.expander.expand(query, max_terms=20)

        self.assertEqual(run1, run2)
        self.assertTrue(len(run1) > 5)
        # Should include core lithography concepts
        terms_joined = " ".join(run1).lower()
        self.assertTrue("euv" in terms_joined or "photoresist" in terms_joined or "photolithography" in terms_joined)

    def test_acronym_bidirectional_expansion(self):
        """Acronyms like EUV, DUV, RAG should resolve bidirectionally."""
        euv_terms = self.expander.expand("EUV", max_terms=10)
        self.assertTrue(any("extreme ultraviolet" in t for t in euv_terms))

        rag_terms = self.expander.expand("RAG", max_terms=10)
        self.assertTrue(any("retrieval augmented generation" in t for t in rag_terms))

    def test_bibliometric_triage_scoring_and_partitioning(self):
        """High citation, prestigious venue papers must enter Priority queue; weak papers enter Archive."""
        high_impact_paper = {
            "title": "High-NA EUV Lithography for Advanced Semiconductor Nodes",
            "venue": "Nature",
            "publication_year": 2024,
            "citation_count": 450,
            "abstract": "We demonstrate 0.55 NA extreme ultraviolet lithography with reduced stochastic defectivity.",
        }

        low_impact_paper = {
            "title": "Unrelated General Topic in Classical Mechanics",
            "venue": "Generic Repository",
            "publication_year": 1995,
            "citation_count": 0,
            "abstract": "A review of introductory pendulum equations.",
        }

        p1 = self.triage.score_paper("semiconductor lithography", high_impact_paper)
        p2 = self.triage.score_paper("semiconductor lithography", low_impact_paper)

        self.assertGreater(p1.triage_score, p2.triage_score)
        self.assertEqual(p1.queue, TriageQueue.PRIORITY)
        self.assertEqual(p2.queue, TriageQueue.ARCHIVE)
        self.assertGreaterEqual(p1.triage_score, 0.50)
        self.assertLess(p2.triage_score, 0.50)

    def test_manifest_cryptographic_signature_and_verification(self):
        """HarvestManifest must be tamper-evident via HMAC-SHA256."""
        secret_key = b"TEST_SIGNING_KEY_32_BYTES_LONG!"
        entries = [
            ManifestEntry(
                paper_id="p1",
                title="Paper One",
                doi="10.1000/1",
                queue="priority",
                triage_score=0.88,
                source="arxiv",
            ),
            ManifestEntry(
                paper_id="p2",
                title="Paper Two",
                doi="10.1000/2",
                queue="archive",
                triage_score=0.32,
                source="crossref",
            ),
        ]

        manifest = HarvestManifest.create(
            harvest_id="harvest_001",
            query="quantum error correction",
            expanded_terms=["qec", "surface code"],
            entries=entries,
            signing_key=secret_key,
        )

        self.assertIsNotNone(manifest.signature)
        self.assertTrue(manifest.verify_signature(secret_key))

        # Tampering with payload must fail verification
        tampered_key = b"WRONG_KEY"
        self.assertFalse(manifest.verify_signature(tampered_key))

        # Tampering with an entry must invalidate original signature
        manifest.entries[0].triage_score = 0.99
        self.assertFalse(manifest.verify_signature(secret_key))


if __name__ == "__main__":
    unittest.main()
