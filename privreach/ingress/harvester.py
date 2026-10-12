"""
Academic Harvester Orchestrator.

Integrates:
1. Deterministic Taxonomy Expander (Zero-LLM domain graph traversal)
2. Multi-Source Harvester (arXiv, OpenAlex, CrossRef)
3. Mathematical Bibliometric Triage (citations, venue impact, recency decay, term relevance)
4. Queue Segregation (Priority vs. Archive)
5. Signed Manifest Generation (HMAC-SHA256 data diode guard)
"""

from typing import List, Dict, Any, Optional
import os
import uuid
import asyncio
from datetime import datetime

from privreach.ingress.taxonomy_expander import DeterministicTaxonomyExpander
from privreach.ingress.bibliometric_triage import BibliometricTriageEngine, TriagedPaper, TriageQueue
from privreach.ingress.manifest import HarvestManifest, ManifestEntry
from privreach.ingress.sources.arxiv_client import ArxivClient
from privreach.ingress.sources.openalex_client import OpenAlexClient
from privreach.ingress.sources.crossref_client import CrossRefClient


class AcademicHarvester:
    """
    Coordinates end-to-end academic paper discovery and triaging.
    Runs strictly in the network-connected Ingress sandbox.
    """

    def __init__(
        self,
        quarantine_dir: str = "quarantine_inbox",
        signing_key: Optional[bytes] = None,
        priority_threshold: float = 0.45,
    ):
        self.quarantine_dir = quarantine_dir
        self.signing_key = signing_key or b"PRIVREACH_INGRESS_AIRLOCK_SECRET_V1"
        self.priority_threshold = priority_threshold

        self.expander = DeterministicTaxonomyExpander()
        self.triage_engine = BibliometricTriageEngine(priority_threshold=priority_threshold)
        self.arxiv_client = ArxivClient()
        self.openalex_client = OpenAlexClient()
        self.crossref_client = CrossRefClient()

        os.makedirs(self.quarantine_dir, exist_ok=True)

    def harvest(
        self,
        query: str,
        max_papers_per_source: int = 15,
        download_priority_pdfs: bool = False,
    ) -> HarvestManifest:
        """
        Synchronous harvest execution.
        """
        return asyncio.run(self.harvest_async(query, max_papers_per_source, download_priority_pdfs))

    async def harvest_async(
        self,
        query: str,
        max_papers_per_source: int = 15,
        download_priority_pdfs: bool = False,
    ) -> HarvestManifest:
        """
        Asynchronously discovers, scores, segregates, and manifests papers for a research topic.
        """
        harvest_id = f"harvest_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

        # 1. Deterministic Taxonomy Expansion
        expanded_terms = self.expander.expand(query, max_terms=25)

        # 2. Query Academic Sources Concurrently
        top_terms_query = " ".join(expanded_terms[:3]) if expanded_terms else query

        tasks = [
            self.arxiv_client.search_async(top_terms_query, max_results=max_papers_per_source),
            self.openalex_client.search_async(top_terms_query, per_page=max_papers_per_source),
            self.crossref_client.search_async(top_terms_query, rows=max_papers_per_source),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        raw_papers: List[Dict[str, Any]] = []
        for r in results:
            if isinstance(r, list):
                raw_papers.extend(r)

        # 3. Deduplication by DOI and normalized title
        seen_dois = set()
        seen_titles = set()
        unique_papers: List[Dict[str, Any]] = []

        for p in raw_papers:
            doi = (p.get("doi") or "").lower().strip()
            norm_title = "".join(c for c in p.get("title", "").lower() if c.isalnum())

            if doi and doi in seen_dois:
                continue
            if norm_title and norm_title in seen_titles:
                continue

            if doi:
                seen_dois.add(doi)
            if norm_title:
                seen_titles.add(norm_title)
            unique_papers.append(p)

        # 4. Bibliometric Triaging & Queue Segregation
        triaged_papers: List[TriagedPaper] = self.triage_engine.triage_corpus(query, unique_papers)

        # 5. Build Manifest Entries
        entries: List[ManifestEntry] = []
        for tp in triaged_papers:
            entry = ManifestEntry(
                paper_id=tp.paper_id,
                title=tp.title,
                doi=tp.doi,
                queue=tp.queue.value,
                triage_score=tp.triage_score,
                source=tp.source,
                pdf_filename=None,
                pdf_sha256=None,
                pdf_size_bytes=0,
                download_status="pending",
            )

            # 6. Optional PDF Download for Priority items
            if download_priority_pdfs and tp.queue == TriageQueue.PRIORITY and tp.pdf_url:
                clean_name = f"{tp.paper_id[:32]}.pdf"
                dest_file = os.path.join(self.quarantine_dir, clean_name)
                sha256 = self.arxiv_client.download_pdf(tp.pdf_url, dest_file)
                if sha256:
                    entry.pdf_filename = clean_name
                    entry.pdf_sha256 = sha256
                    entry.pdf_size_bytes = os.path.getsize(dest_file)
                    entry.download_status = "downloaded"
                else:
                    entry.download_status = "failed"

            entries.append(entry)

        # 7. Construct and sign harvest manifest
        manifest = HarvestManifest.create(
            harvest_id=harvest_id,
            query=query,
            expanded_terms=expanded_terms,
            entries=entries,
            signing_key=self.signing_key,
        )

        return manifest
