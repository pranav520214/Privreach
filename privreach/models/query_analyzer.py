"""Query Analyzer: The 0.5B Administrative Router of the RLCD architecture."""

import json
import re
from typing import Optional
from privearch.schemas import QueryAnalysis, RiskLevel, TaskType
from privearch.models.client import LocalModelClient


QUERY_ROUTER_SYSTEM_PROMPT = """You are Privearch OS Query Analyzer, a fast administrative router for scientific and chemical literature.
Analyze the user's scientific query and output ONLY a single valid JSON object. Do not include markdown commentary.

Schema fields:
{
  "risk_level": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
  "task_type": "LITERATURE_REVIEW" | "MECHANISTIC_SYNTHESIS" | "FACT_CHECK" | "SAFETY_AUDIT" | "CALCULATION_DERIVATION" | "DEFINITION_EXTRACTION",
  "scientific_domain": "Domain name (e.g. Physical Chemistry, Toxicology, Organic Chemistry)",
  "key_entities": ["list of chemicals, formulas, laws, or terms"],
  "lexical_keywords": ["3-5 high-signal exact keywords for BM25 lexical search"],
  "semantic_queries": ["1-2 expanded scientific questions for semantic vector search"],
  "adversarial_audit_required": true | false,
  "analysis_rationale": "one sentence explaining risk and focus"
}

Risk Guidelines:
- CRITICAL: Toxicity, poison, explosive hazard, violent reactions, lethal doses, reactive chemicals.
- HIGH: Reaction mechanisms, non-equilibrium states, thermodynamic constants, quantitative laws.
- MEDIUM: Standard literature review, properties, definitions, comparison of theories.
- LOW: General index queries, table of contents, simple factual terminology.
"""


class QueryAnalyzer:
    """
    RLCD Router:
    Intercepts the user query using the 0.5B model and tags it with a Pydantic schema.
    """
    def __init__(self, client: LocalModelClient, model_name: str = "qwen2.5:0.5b"):
        self.client = client
        self.model_name = model_name

    def analyze(self, query: str) -> QueryAnalysis:
        prompt = f"Analyze this scientific query:\n\"{query}\"\n\nJSON:"

        try:
            raw_output = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                system=QUERY_ROUTER_SYSTEM_PROMPT,
                temperature=0.1,
                max_tokens=256
            )
            return self._parse_json_to_schema(raw_output, query)
        except Exception as e:
            # Safe heuristic fallback if model fails
            return self._heuristic_fallback(query, str(e))

    def _parse_json_to_schema(self, raw_output: str, query: str) -> QueryAnalysis:
        """Extract and validate JSON into QueryAnalysis schema."""
        # Find JSON block using regex
        json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(0))
                # Validate enum values
                risk = data.get("risk_level", "MEDIUM").upper()
                if risk not in [r.value for r in RiskLevel]:
                    risk = "MEDIUM"

                task = data.get("task_type", "LITERATURE_REVIEW").upper()
                if task not in [t.value for t in TaskType]:
                    task = "LITERATURE_REVIEW"

                return QueryAnalysis(
                    risk_level=RiskLevel(risk),
                    task_type=TaskType(task),
                    scientific_domain=data.get("scientific_domain", "Chemistry"),
                    key_entities=data.get("key_entities", []),
                    lexical_keywords=data.get("lexical_keywords", query.split()[:4]),
                    semantic_queries=data.get("semantic_queries", [query]),
                    adversarial_audit_required=bool(data.get("adversarial_audit_required", True)),
                    analysis_rationale=data.get("analysis_rationale", "Standard administrative routing.")
                )
            except Exception:
                pass

        return self._heuristic_fallback(query, "JSON parsing error")

    def _heuristic_fallback(self, query: str, reason: str) -> QueryAnalysis:
        """Rule-based safety fallback for 0.5B model."""
        q_lower = query.lower()
        is_critical = any(w in q_lower for w in ["toxic", "hazard", "explosive", "poison", "dangerous", "lethal", "acid burn"])
        is_high = any(w in q_lower for w in ["mechanism", "equilibrium", "constant", "rate", "calculate", "derivation"])

        if is_critical:
            risk = RiskLevel.CRITICAL
        elif is_high:
            risk = RiskLevel.HIGH
        else:
            risk = RiskLevel.MEDIUM

        words = [w for w in re.findall(r'\b\w+\b', query) if len(w) > 3]

        return QueryAnalysis(
            risk_level=risk,
            task_type=TaskType.MECHANISTIC_SYNTHESIS if is_high else TaskType.LITERATURE_REVIEW,
            scientific_domain="Chemistry / Physical Sciences",
            key_entities=words[:4],
            lexical_keywords=words[:5],
            semantic_queries=[query],
            adversarial_audit_required=True,
            analysis_rationale=f"Heuristic fallback activated ({reason})."
        )
