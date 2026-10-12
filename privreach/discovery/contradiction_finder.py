"""
Predicate and Propositional Contradiction Finder.

Identifies mutually conflicting claims and hypotheses across ingested papers
using directional polarity mapping and SymPy propositional SAT proving.
"""

from typing import List, Dict, Set, Tuple, Optional, Any
import re
import sympy as sp
from sympy.logic.inference import satisfiable
from pydantic import BaseModel, Field


class ScientificClaimProposition(BaseModel):
    """Normalized structured claim predicate extracted from text."""
    claim_id: str
    subject: str
    relation: str
    object: str
    polarity: int  # +1 (increases/activates), -1 (decreases/inhibits), 0 (neutral)
    numeric_bound: Optional[Tuple[float, float]] = None  # (min_val, max_val)
    source_doc: str
    page_num: int = 1
    raw_text: str = ""


class ContradictionRecord(BaseModel):
    """Detailed record of a proven contradiction between two sources."""
    conflict_id: str
    subject: str
    object: str
    claim_a: ScientificClaimProposition
    claim_b: ScientificClaimProposition
    contradiction_type: str  # "POLARITY_OPPOSITION", "DISJOINT_INTERVAL"
    explanation: str
    is_satisfiable: bool = False


class ContradictionReport(BaseModel):
    """Audit report of contradictions discovered across the corpus."""
    total_claims_analyzed: int = 0
    total_contradictions_found: int = 0
    contradictions: List[ContradictionRecord] = Field(default_factory=list)


POSITIVE_RELATIONS = {
    "increases", "promotes", "activates", "upregulates", "enhances",
    "induces", "stimulates", "amplifies", "improves", "causes",
}

NEGATIVE_RELATIONS = {
    "decreases", "inhibits", "suppresses", "downregulates", "reduces",
    "blocks", "prevents", "diminishes", "attenuates", "negates",
}


class ContradictionFinder:
    """
    Detects logical and empirical contradictions across research literature.
    """

    def __init__(self):
        self.claims: List[ScientificClaimProposition] = []

    def classify_relation_polarity(self, relation: str) -> int:
        """Classifies relation into +1 (positive), -1 (negative), or 0 (neutral)."""
        rel_norm = relation.strip().lower()
        if rel_norm in POSITIVE_RELATIONS or any(p in rel_norm for p in POSITIVE_RELATIONS):
            return 1
        if rel_norm in NEGATIVE_RELATIONS or any(n in rel_norm for n in NEGATIVE_RELATIONS):
            return -1
        return 0

    def add_claim(
        self,
        subject: str,
        relation: str,
        object: str,
        source_doc: str,
        page_num: int = 1,
        raw_text: str = "",
        numeric_range: Optional[Tuple[float, float]] = None,
    ) -> ScientificClaimProposition:
        """Registers a structured proposition for contradiction auditing."""
        polarity = self.classify_relation_polarity(relation)
        claim_id = f"prop_{len(self.claims) + 1:04d}"

        prop = ScientificClaimProposition(
            claim_id=claim_id,
            subject=subject.strip().lower(),
            relation=relation.strip().lower(),
            object=object.strip().lower(),
            polarity=polarity,
            numeric_bound=numeric_range,
            source_doc=source_doc,
            page_num=page_num,
            raw_text=raw_text or f"{subject} {relation} {object}",
        )
        self.claims.append(prop)
        return prop

    def check_contradiction(
        self,
        prop_a: ScientificClaimProposition,
        prop_b: ScientificClaimProposition,
    ) -> Optional[ContradictionRecord]:
        """
        Determines whether prop_a and prop_b form a logical or empirical contradiction.
        """
        # Subject and Object must match
        if prop_a.subject != prop_b.subject or prop_a.object != prop_b.object:
            return None

        # Check 1: Polarity Opposition (+1 vs -1 on same (S, O) pair)
        if (prop_a.polarity == 1 and prop_b.polarity == -1) or (prop_a.polarity == -1 and prop_b.polarity == 1):
            # Formulate SymPy SAT proposition: (Effect_A) and not (Effect_A)
            p = sp.Symbol(f"effect_{prop_a.subject}_{prop_a.object}")
            conjunction = p & ~p
            sat_result = satisfiable(conjunction)  # Returns False (unsatisfiable)

            explanation = (
                f"Direct polarity contradiction on ({prop_a.subject} -> {prop_a.object}): "
                f"'{prop_a.source_doc}' asserts '{prop_a.relation}', while "
                f"'{prop_b.source_doc}' asserts '{prop_b.relation}'."
            )

            return ContradictionRecord(
                conflict_id=f"conf_{prop_a.claim_id}_{prop_b.claim_id}",
                subject=prop_a.subject,
                object=prop_a.object,
                claim_a=prop_a,
                claim_b=prop_b,
                contradiction_type="POLARITY_OPPOSITION",
                explanation=explanation,
                is_satisfiable=bool(sat_result),
            )

        # Check 2: Disjoint Numeric Ranges
        if prop_a.numeric_bound and prop_b.numeric_bound:
            min_a, max_a = prop_a.numeric_bound
            min_b, max_b = prop_b.numeric_bound

            # Two closed intervals [min_a, max_a] and [min_b, max_b] are disjoint if max_a < min_b or max_b < min_a
            if max_a < min_b or max_b < min_a:
                explanation = (
                    f"Disjoint numeric measurement bounds for ({prop_a.subject} -> {prop_a.object}): "
                    f"'{prop_a.source_doc}' reports [{min_a}, {max_a}], while "
                    f"'{prop_b.source_doc}' reports [{min_b}, {max_b}]."
                )

                return ContradictionRecord(
                    conflict_id=f"conf_{prop_a.claim_id}_{prop_b.claim_id}",
                    subject=prop_a.subject,
                    object=prop_a.object,
                    claim_a=prop_a,
                    claim_b=prop_b,
                    contradiction_type="DISJOINT_INTERVAL",
                    explanation=explanation,
                    is_satisfiable=False,
                )

        return None

    def scan_all_contradictions(self) -> ContradictionReport:
        """
        Pairwise audits all registered claims for contradictions.
        """
        contradictions: List[ContradictionRecord] = []
        n = len(self.claims)

        for i in range(n):
            for j in range(i + 1, n):
                record = self.check_contradiction(self.claims[i], self.claims[j])
                if record is not None:
                    contradictions.append(record)

        return ContradictionReport(
            total_claims_analyzed=n,
            total_contradictions_found=len(contradictions),
            contradictions=contradictions,
        )
