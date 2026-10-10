"""Deep Scientific Synthesis Engine: The 4B Model with R1 / CoT Reasoning Integration."""

import re
import time
from typing import List, Optional, Tuple, Iterator, Any
from privearch.schemas import ScoredChunk, QueryAnalysis, ReasoningStep, TaskType, RiskLevel
from privearch.models.client import LocalModelClient
from privearch.models.reasoning_engine import (
    ReasoningEngine,
    REASONING_SYSTEM_PROMPT,
    extract_thought_trace,
    is_reasoning_model
)


SYNTHESIS_SYSTEM_PROMPT = """You are Privearch OS Synthesis Engine, an academic scientific synthesis intelligence.
Your task is to produce a rigorous, peer-review quality scientific answer based strictly on the provided literature passages.

MANDATORY SCIENTIFIC ACCURACY RULES:
1. Grounding: Every single claim, chemical property, equation, and parameter MUST come directly from the provided passages.
2. Citations: You MUST use bracket citations like [1], [2] immediately following every factual statement or numerical value.
3. Anti-Hallucination: Do NOT guess, speculate, or fabricate numbers, reaction rates, or physical constants. If the provided passages do not state a specific fact, explicitly write: "(Not specified in provided literature [N])".
4. Formatting: Structure your response cleanly with clear section headings, bolded scientific terms, and explicit chemical equations.
"""


class SynthesisOutput:
    """Wrapper holding synthesized academic text along with optional deep thinking trace."""
    def __init__(
        self,
        text: str,
        thought_trace: Optional[str] = None,
        reasoning_steps: Optional[List[ReasoningStep]] = None,
        duration_s: float = 0.0
    ):
        self.text = text
        self.thought_trace = thought_trace
        self.reasoning_steps = reasoning_steps or []
        self.duration_s = duration_s

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return f"<SynthesisOutput text_len={len(self.text)} has_thinking={bool(self.thought_trace)}>"

    def __iter__(self) -> Iterator[Any]:
        yield self.text
        yield self.thought_trace
        yield self.reasoning_steps
        yield self.duration_s


class SynthesisEngine:
    """
    RLCD Control:
    Reads retrieved scientific passages and synthesizes an academic, citation-grounded response
    with optional R1 / CoT multi-step chain-of-thought deliberation.
    """
    def __init__(self, client: LocalModelClient, model_name: str = "qwen2.5-coder:3b"):
        self.client = client
        self.model_name = model_name
        self.reasoning_engine = ReasoningEngine()

    def synthesize(
        self,
        query: str,
        query_analysis: QueryAnalysis,
        retrieved_chunks: List[ScoredChunk],
        injected_calc_context: str = "",
        deep_thinking: bool = True
    ) -> SynthesisOutput:
        """Synthesize answer with bracketed citations and optional R1 / CoT thought stream."""
        # Guardrail Interceptor: Refuse dangerous CBRN / chemical weapon synthesis requests
        if query_analysis.task_type == TaskType.SAFETY_AUDIT and "SAFETY REFUSAL" in getattr(query_analysis, "analysis_rationale", ""):
            refusal_text = (
                "### 🛡️ Privreach OS Safety & Biosecurity Guardrail Policy\n\n"
                f"> **Security Notice:** {query_analysis.analysis_rationale}\n\n"
                "Privreach OS operates under strict defensive biosecurity and chemical weapon non-proliferation guardrails. "
                "The requested procedure involves hazardous or restricted toxic/weaponized agents and cannot be synthesized. "
                "For legitimate toxicology research, please consult official safety data sheets (MSDS/OSHA) or designated institutional biosafety officers."
            )
            return SynthesisOutput(text=refusal_text, duration_s=0.01)

        if not retrieved_chunks:
            calc_intro = ""
            if injected_calc_context:
                calc_intro = f"\n{injected_calc_context}\n\n"
            base_prompt = (
                f"You are Privreach OS. Answer the following scientific research inquiry accurately.\n"
                f"{calc_intro}"
                f"Query: {query}\n\nAnswer:"
            )
            try:
                direct_ans = self.client.generate(
                    self.model_name,
                    prompt=base_prompt,
                    system=SYNTHESIS_SYSTEM_PROMPT,
                    max_tokens=1024
                )
            except Exception as e:
                direct_ans = f"Local model inference error: {e}"
            return SynthesisOutput(
                text=(
                    "> ⚠️ **Notice: Knowledge Vault is empty.**\n"
                    "> Ingest a PDF document or textbook (via drag-and-drop or PDF Ingester) to enable literature-grounded RLCD verification.\n\n"
                    + direct_ans
                )
            )

        t_start = time.time()
        is_r1 = is_reasoning_model(self.model_name)

        if deep_thinking or is_r1:
            prompt = self.reasoning_engine.build_reasoning_prompt(
                query=query,
                query_analysis=query_analysis,
                retrieved_chunks=retrieved_chunks,
                injected_calc_context=injected_calc_context
            )
            system = REASONING_SYSTEM_PROMPT
            max_tokens = 2048  # Allow ample headroom for CoT + synthesis
        else:
            # Format context passages with citation indices [1], [2], ...
            passages_text = []
            for i, sc in enumerate(retrieved_chunks, start=1):
                c = sc.chunk
                ev_type = getattr(c, "evidence_type", "DOCUMENT_PAGE")
                header = f"[{i}] Document: {c.doc_name} | Page: {c.page_num}"
                if c.section_header:
                    header += f" | Section: {c.section_header}"
                if ev_type != "DOCUMENT_PAGE":
                    header += f" | Type: {ev_type}"
                passages_text.append(f"{header}\n\"\"\"\n{c.text}\n\"\"\"")

            context_block = "\n\n".join(passages_text)
            prompt = (
                f"SCIENTIFIC QUERY:\n{query}\n\n"
                f"DOMAIN: {query_analysis.scientific_domain} (Risk: {query_analysis.risk_level.value})\n"
                f"TASK: {query_analysis.task_type.value}\n\n"
                f"RETRIEVED SOURCE PASSAGES:\n"
                f"{context_block}\n"
                f"{injected_calc_context}\n\n"
                f"INSTRUCTIONS:\n"
                f"Synthesize a rigorous, publication-grade academic answer to the query using ONLY the facts above.\n"
                f"Cite each supporting passage using [1], [2], etc. immediately after every assertion.\n\n"
                f"SCIENTIFIC SYNTHESIS:"
            )
            system = SYNTHESIS_SYSTEM_PROMPT
            max_tokens = 1024

        raw_output = self.client.generate(
            model=self.model_name,
            prompt=prompt,
            system=system,
            temperature=0.15,
            max_tokens=max_tokens
        )
        elapsed_thinking = round(time.time() - t_start, 2)

        # Extract <think>...</think> stream from synthesis text
        clean_synthesis, thought_trace = extract_thought_trace(raw_output)

        # If thought trace was extracted, decompose into structured cognitive stages
        reasoning_steps: List[ReasoningStep] = []
        if thought_trace:
            reasoning_steps = self.reasoning_engine.decompose_reasoning_steps(
                thought_trace=thought_trace,
                query=query,
                retrieved_chunks=retrieved_chunks
            )

        final_text = clean_synthesis
        if not final_text and raw_output:
            final_text = re.sub(r'</?think>', '', raw_output, flags=re.IGNORECASE)
            final_text = re.sub(r'^#+\s*<think>', '', final_text, flags=re.IGNORECASE).strip()

        return SynthesisOutput(
            text=final_text or raw_output,
            thought_trace=thought_trace,
            reasoning_steps=reasoning_steps,
            duration_s=elapsed_thinking
        )
