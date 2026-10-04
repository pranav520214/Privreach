"""Deep Scientific Synthesis Engine: The 4B Model of the RLCD Architecture."""

from typing import List
from privearch.schemas import ScoredChunk, QueryAnalysis
from privearch.models.client import LocalModelClient


SYNTHESIS_SYSTEM_PROMPT = """You are Privearch OS Synthesis Engine, an academic scientific synthesis intelligence.
Your task is to produce a rigorous, peer-review quality scientific answer based strictly on the provided literature passages.

MANDATORY SCIENTIFIC ACCURACY RULES:
1. Grounding: Every single claim, chemical property, equation, and parameter MUST come directly from the provided passages.
2. Citations: You MUST use bracket citations like [1], [2] immediately following every factual statement or numerical value.
3. Anti-Hallucination: Do NOT guess, speculate, or fabricate numbers, reaction rates, or physical constants. If the provided passages do not state a specific fact, explicitly write: "(Not specified in provided literature [N])".
4. Formatting: Structure your response cleanly with clear section headings, bolded scientific terms, and explicit chemical equations.
"""


class SynthesisEngine:
    """
    RLCD Control:
    Reads retrieved scientific passages and synthesizes an academic, citation-grounded response.
    """
    def __init__(self, client: LocalModelClient, model_name: str = "qwen2.5-coder:3b"):
        self.client = client
        self.model_name = model_name

    def synthesize(
        self,
        query: str,
        query_analysis: QueryAnalysis,
        retrieved_chunks: List[ScoredChunk]
    ) -> str:
        """Synthesize answer with bracketed citations."""
        if not retrieved_chunks:
            return (
                "### Ingestion Required\n\n"
                "No scientific documents have been ingested yet into the RAM index. "
                "Please drag and drop a PDF into Privearch to enable zero-hallucination synthesis."
            )

        # Format context passages with citation indices [1], [2], ...
        passages_text = []
        for i, sc in enumerate(retrieved_chunks, start=1):
            c = sc.chunk
            ev_type = getattr(c, "evidence_type", "DOCUMENT_PAGE")
            if ev_type in ("VIDEO_TIMECODE", "AUDIO_TRANSCRIPT"):
                header = f"[{i}] Media: {c.doc_name} | Type: {ev_type}"
                if c.section_header:
                    header += f" | Timecode: {c.section_header}"
                if getattr(c, "speaker_id", None):
                    header += f" | Speaker: {c.speaker_id}"
            else:
                header = f"[{i}] Document: {c.doc_name} | Page: {c.page_num}"
                if c.section_header:
                    header += f" | Section: {c.section_header}"
            passages_text.append(f"{header}\n\"\"\"\n{c.text}\n\"\"\"")

        context_block = "\n\n".join(passages_text)

        prompt = (
            f"SCIENTIFIC QUERY:\n{query}\n\n"
            f"DOMAIN: {query_analysis.scientific_domain} (Risk: {query_analysis.risk_level.value})\n"
            f"TASK: {query_analysis.task_type.value}\n\n"
            f"RETRIEVED SOURCE PASSAGES:\n"
            f"{context_block}\n\n"
            f"INSTRUCTIONS:\n"
            f"Synthesize a rigorous, publication-grade academic answer to the query using ONLY the facts above.\n"
            f"Cite each supporting passage using [1], [2], etc. immediately after every assertion.\n\n"
            f"SCIENTIFIC SYNTHESIS:"
        )

        output = self.client.generate(
            model=self.model_name,
            prompt=prompt,
            system=SYNTHESIS_SYSTEM_PROMPT,
            temperature=0.15,
            max_tokens=1024
        )
        return output
