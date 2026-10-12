"""
privreach.ingress: Deterministic Academic Harvester Subsystem.

Responsible for:
- Deterministic multi-ontology taxonomy expansion (Zero-LLM)
- Multi-source paper harvesting (arXiv, OpenAlex, CrossRef)
- Mathematical bibliometric triage scoring (citation impact, venue quality, recency, relevance)
- Segregation into Prioritized vs. Unprioritized archive queues
- Cryptographic harvest manifest generation with hash verification
"""

from privreach.ingress.taxonomy_expander import DeterministicTaxonomyExpander
from privreach.ingress.bibliometric_triage import BibliometricTriageEngine, TriagedPaper, TriageQueue
from privreach.ingress.manifest import HarvestManifest, ManifestEntry
from privreach.ingress.harvester import AcademicHarvester

__all__ = [
    "DeterministicTaxonomyExpander",
    "BibliometricTriageEngine",
    "TriagedPaper",
    "TriageQueue",
    "HarvestManifest",
    "ManifestEntry",
    "AcademicHarvester",
]
