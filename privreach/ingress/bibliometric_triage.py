"""
Deterministic Bibliometric Triage Scoring Engine.

Implements mathematical ranking and queue partitioning for academic papers:
S(p) = alpha * log10(C_p + 1) + beta * venue_score + gamma * e^(-lambda * delta_years) + delta * sim(q, abstract)

Partitions papers deterministically into:
- Priority Queue: S(p) >= threshold (promoted to Airlock security verification)
- Archive Queue: S(p) < threshold (stored in cold storage repository)
"""

from typing import List, Dict, Any, Optional
from enum import Enum
import math
import re
from datetime import datetime
from pydantic import BaseModel, Field


class TriageQueue(str, Enum):
    PRIORITY = "priority"
    ARCHIVE = "archive"


class TriagedPaper(BaseModel):
    """Normalized metadata record for a triaged research paper."""
    paper_id: str
    title: str
    authors: List[str] = Field(default_factory=list)
    abstract: str = ""
    doi: Optional[str] = None
    venue: str = ""
    publication_year: int = 2024
    citation_count: int = 0
    pdf_url: Optional[str] = None
    source: str = "unknown"  # arxiv, openalex, crossref, manual
    triage_score: float = 0.0
    queue: TriageQueue = TriageQueue.ARCHIVE
    score_breakdown: Dict[str, float] = Field(default_factory=dict)


# High-impact venues in STEM with prestige tier scores [0.0 - 1.0]
PRESTIGE_VENUE_WEIGHTS: Dict[str, float] = {
    # Flagship Multi-disciplinary
    "nature": 1.00,
    "science": 1.00,
    "proceedings of the national academy of sciences": 0.90,
    "pnas": 0.90,
    "nature communications": 0.92,
    "science advances": 0.92,

    # Semiconductor & Device Physics
    "ieee transactions on electron devices": 0.88,
    "ieee electron device letters": 0.85,
    "applied physics letters": 0.82,
    "journal of vacuum science & technology": 0.80,
    "spie advanced lithography": 0.85,
    "ieee journal of solid-state circuits": 0.92,
    "iedm": 0.95,
    "vlsit": 0.92,
    "isscc": 0.95,

    # Physics & Materials
    "physical review letters": 0.95,
    "physical review b": 0.85,
    "advanced materials": 0.93,
    "nano letters": 0.90,
    "acs nano": 0.90,

    # Computer Science & AI
    "neurips": 0.95,
    "icml": 0.95,
    "iclr": 0.95,
    "cvpr": 0.95,
    "acm computing surveys": 0.90,
    "ieee transactions on pattern analysis and machine intelligence": 0.95,

    # Preprints / Generic Repositories
    "arxiv": 0.65,
    "biorxiv": 0.65,
    "medrxiv": 0.65,
}


class BibliometricTriageEngine:
    """
    Computes mathematical confidence and impact scores for harvested documents.
    No generative LLM bias: uses purely verifiable bibliometrics and text overlap.
    """

    def __init__(
        self,
        alpha_citations: float = 0.30,
        beta_venue: float = 0.20,
        gamma_recency: float = 0.25,
        delta_relevance: float = 0.25,
        decay_lambda: float = 0.15,
        priority_threshold: float = 0.45,
        current_year: Optional[int] = None,
    ):
        self.alpha = alpha_citations
        self.beta = beta_venue
        self.gamma = gamma_recency
        self.delta = delta_relevance
        self.decay_lambda = decay_lambda
        self.priority_threshold = priority_threshold
        self.current_year = current_year or datetime.now().year

    def calculate_citation_score(self, citation_count: int, max_citations_scale: float = 5.0) -> float:
        """
        Normalized citation impact on logarithmic scale.
        log10(citations + 1) / 5.0 (clamps to 1.0 for ~100k+ citations).
        """
        if citation_count <= 0:
            return 0.0
        log_val = math.log10(citation_count + 1)
        return min(1.0, log_val / max_citations_scale)

    def calculate_venue_score(self, venue_name: str) -> float:
        """Looks up venue prestige weight using normalized fuzzy substring matching."""
        if not venue_name:
            return 0.30  # Default unindexed venue baseline
        norm_venue = venue_name.lower().strip()

        # Exact match
        if norm_venue in PRESTIGE_VENUE_WEIGHTS:
            return PRESTIGE_VENUE_WEIGHTS[norm_venue]

        # Substring match
        for key, weight in PRESTIGE_VENUE_WEIGHTS.items():
            if key in norm_venue or norm_venue in key:
                return weight

        return 0.40  # Standard peer-reviewed conference/journal baseline

    def calculate_recency_score(self, pub_year: int) -> float:
        """
        Exponential recency decay:
        recency = e^(-lambda * (current_year - pub_year))
        """
        delta_years = max(0, self.current_year - pub_year)
        return math.exp(-self.decay_lambda * delta_years)

    def calculate_relevance_score(self, query: str, title: str, abstract: str) -> float:
        """
        Calculates deterministic lexical relevance of query terms against title and abstract.
        Title matches receive 3x weighting over abstract matches.
        """
        q_tokens = set(re.findall(r"\w+", query.lower()))
        if not q_tokens:
            return 0.50

        title_tokens = set(re.findall(r"\w+", title.lower()))
        abstract_tokens = set(re.findall(r"\w+", abstract.lower()))

        title_hits = sum(1 for t in q_tokens if t in title_tokens)
        abstract_hits = sum(1 for t in q_tokens if t in abstract_tokens)

        # Weighted overlap
        total_tokens = len(q_tokens)
        title_ratio = title_hits / total_tokens
        abstract_ratio = abstract_hits / total_tokens

        # Title is 3x more salient than abstract
        score = (3.0 * title_ratio + 1.0 * abstract_ratio) / 4.0
        return min(1.0, score)

    def score_paper(self, query: str, paper_dict: Dict[str, Any]) -> TriagedPaper:
        """
        Scores an individual paper and assigns it to either Priority or Archive queue.
        """
        citation_count = int(paper_dict.get("citation_count", 0))
        pub_year = int(paper_dict.get("publication_year", self.current_year))
        venue = str(paper_dict.get("venue", ""))
        title = str(paper_dict.get("title", ""))
        abstract = str(paper_dict.get("abstract", ""))

        c_score = self.calculate_citation_score(citation_count)
        v_score = self.calculate_venue_score(venue)
        r_score = self.calculate_recency_score(pub_year)
        rel_score = self.calculate_relevance_score(query, title, abstract)

        composite_score = (
            self.alpha * c_score
            + self.beta * v_score
            + self.gamma * r_score
            + self.delta * rel_score
        )
        composite_score = round(min(1.0, max(0.0, composite_score)), 4)

        assigned_queue = (
            TriageQueue.PRIORITY
            if composite_score >= self.priority_threshold
            else TriageQueue.ARCHIVE
        )

        breakdown = {
            "citation_impact": round(c_score, 4),
            "venue_prestige": round(v_score, 4),
            "recency_decay": round(r_score, 4),
            "query_relevance": round(rel_score, 4),
            "final_score": composite_score,
        }

        return TriagedPaper(
            paper_id=str(paper_dict.get("paper_id") or paper_dict.get("doi") or f"paper_{hash(title)}"),
            title=title,
            authors=paper_dict.get("authors", []),
            abstract=abstract,
            doi=paper_dict.get("doi"),
            venue=venue,
            publication_year=pub_year,
            citation_count=citation_count,
            pdf_url=paper_dict.get("pdf_url"),
            source=paper_dict.get("source", "unknown"),
            triage_score=composite_score,
            queue=assigned_queue,
            score_breakdown=breakdown,
        )

    def triage_corpus(self, query: str, papers: List[Dict[str, Any]]) -> List[TriagedPaper]:
        """
        Scores and ranks a list of papers, returning them ordered by triage score descending.
        """
        scored = [self.score_paper(query, p) for p in papers]
        scored.sort(key=lambda p: p.triage_score, reverse=True)
        return scored
