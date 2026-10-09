"""Privearch OS Engine: The RLCD Orchestration Kernel."""

import time
import os
import psutil
from typing import List, Dict, Any, Optional

from privearch.config import PrivearchConfig, DEFAULT_CONFIG
from privearch.schemas import (

    DocumentChunk,
    ScoredChunk,
    QueryAnalysis,
    VerificationAudit,
    PrivearchReport,
    CalculationVerification,
    ArtifactRecord,
    ToolCallResult,
    TaskType,
)
from privearch.ingestion.pdf_extractor import extract_pdf
from privearch.ingestion.chunker import chunk_document
from privearch.ingestion.vision_extractor import VisionDocumentExtractor
from privearch.retrieval.embeddings import get_embedding_engine
from privearch.retrieval.bm25 import InRamBM25
from privearch.retrieval.faiss_index import InRamVectorIndex
from privearch.retrieval.hybrid_rrf import HybridRRFRetriever
from privearch.models.client import LocalModelClient
from privearch.models.query_analyzer import QueryAnalyzer
from privearch.models.synthesis_engine import SynthesisEngine
from privearch.models.adversarial_verifier import AdversarialVerifier
from privearch.tools import ToolGraph
from privearch.compute import DeterministicSolver, EquationParser
from privearch.artifacts import ArtifactRegistry
from privearch.multimodal import VideoProcessor, AudioProcessor, MeetingIntelligenceEngine
from privearch.graph import KnowledgeGraphEngine



class PrivearchKernel:
    """
    Privearch Operating System Kernel:
    Manages In-RAM hybrid indexes, CPU embeddings, and the RLCD dual-model pipeline.
    """
    def __init__(self, config: PrivearchConfig = DEFAULT_CONFIG):
        self.config = config

        # 1. Initialize Local Client
        self.client = LocalModelClient(base_url=config.ollama_base_url)

        # Model Selection with Automatic Local Fallbacks
        self.router_model = self.client.select_best_model(
            config.router_model, config.router_fallbacks
        )
        self.synthesis_model = self.client.select_best_model(
            config.synthesis_model, config.synthesis_fallbacks
        )
        self.verifier_model = self.client.select_best_model(
            config.verifier_model, config.verifier_fallbacks
        )

        # 2. In-RAM Hybrid Storage & Retrieval
        self.embedding_engine = get_embedding_engine(
            backend=config.embedding_backend,
            model_name=config.cpu_embedding_model if config.embedding_backend == "cpu_minilm" else config.ollama_embedding_model,
            base_url=config.ollama_base_url
        )

        dim = 384 if config.embedding_backend == "cpu_minilm" else 1024
        self.bm25 = InRamBM25(k1=config.bm25_k1, b=config.bm25_b)
        self.vector_index = InRamVectorIndex(dimension=dim)
        self.hybrid_retriever = HybridRRFRetriever(
            bm25_index=self.bm25,
            vector_index=self.vector_index,
            embedding_engine=self.embedding_engine,
            rrf_k=config.rrf_k
        )

        # 3. RLCD Processors
        self.router = QueryAnalyzer(client=self.client, model_name=self.router_model)
        self.synthesis = SynthesisEngine(client=self.client, model_name=self.synthesis_model)
        self.verifier = AdversarialVerifier(client=self.client, model_name=self.verifier_model)

        # 4. Deterministic Tool Graph, Solver & Artifact Registry
        self.tool_graph = ToolGraph()
        self.solver = DeterministicSolver(sandbox=self.tool_graph.get("python_sandbox"))
        self.artifact_registry = ArtifactRegistry()

        # 5. Multimodal Ingestion & Meeting Intelligence Engines
        self.video_processor = VideoProcessor()
        self.audio_processor = AudioProcessor()
        self.meeting_engine = MeetingIntelligenceEngine(audio_processor=self.audio_processor)

        # 6. Vision Document Extractor (Formulas, Tables, Diagrams)
        self.vision_extractor = VisionDocumentExtractor()

        # 7. In-RAM Knowledge Graph & Cross-Document Citation Engine
        self.graph_engine = KnowledgeGraphEngine()

        # Ingestion state tracking
        self.ingested_files: List[Dict[str, Any]] = []
        self.total_chunks: int = 0
        self.cache_dir = os.path.abspath(".privearch_cache")

        # Automatically load cached index if available
        self.load_index()


    def save_index(self, cache_dir: Optional[str] = None) -> bool:
        """Persist In-RAM hybrid index to disk for instant zero-latency boot."""
        target_dir = cache_dir or self.cache_dir
        os.makedirs(target_dir, exist_ok=True)

        if not self.bm25.chunks or self.vector_index.vectors is None:
            return False

        import json
        import numpy as np

        # 1. Save chunks
        chunks_data = [c.model_dump() for c in self.bm25.chunks]
        with open(os.path.join(target_dir, "chunks.json"), "w", encoding="utf-8") as f:
            json.dump(chunks_data, f, ensure_ascii=False)

        # 2. Save vectors
        np.save(os.path.join(target_dir, "vectors.npy"), self.vector_index.vectors)

        # 3. Save manifest
        manifest = {
            "total_chunks": self.total_chunks,
            "ingested_files": self.ingested_files,
            "embedding_dimension": self.vector_index.dimension,
            "embedding_backend": self.config.embedding_backend
        }
        with open(os.path.join(target_dir, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        # 4. Save Knowledge Graph
        self.graph_engine.save_to_dir(target_dir)

        return True

    def load_index(self, cache_dir: Optional[str] = None) -> bool:
        """Load pre-indexed knowledge vault into RAM in milliseconds."""
        target_dir = cache_dir or self.cache_dir
        chunks_file = os.path.join(target_dir, "chunks.json")
        vectors_file = os.path.join(target_dir, "vectors.npy")
        manifest_file = os.path.join(target_dir, "manifest.json")

        if not (os.path.exists(chunks_file) and os.path.exists(vectors_file) and os.path.exists(manifest_file)):
            return False

        try:
            import json
            import numpy as np

            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            with open(chunks_file, "r", encoding="utf-8") as f:
                raw_chunks = json.load(f)

            chunks = [DocumentChunk(**c) for c in raw_chunks]
            vectors = np.load(vectors_file)

            # Clear current and populate in-RAM
            self.bm25.clear()
            self.vector_index.clear()

            self.bm25.add_chunks(chunks)
            self.vector_index.add_vectors(vectors, chunks)

            # Load or build Knowledge Graph
            if not self.graph_engine.load_from_dir(target_dir):
                self.graph_engine.index_chunks(chunks)

            self.ingested_files = manifest.get("ingested_files", [])
            self.total_chunks = len(chunks)
            return True
        except Exception as e:
            print(f"[Warning] Failed to load index cache: {e}")
            return False

    def ingest_pdf(self, pdf_path: str, force: bool = False, auto_save: bool = True) -> Dict[str, Any]:
        """
        Dynamically ingest a PDF file into RAM:
        Vision Document Extraction (LaTeX formulas, Markdown tables, Visual diagrams, Prose) ->
        Semantic chunking -> CPU embedding -> Update BM25 and FAISS in RAM.
        """
        abs_path = os.path.abspath(pdf_path)
        doc_base = os.path.basename(pdf_path)

        if not force:
            for f in self.ingested_files:
                if f.get("path") == abs_path or f.get("doc_name") == doc_base:
                    return {
                        "status": "already_indexed",
                        "doc_name": doc_base,
                        "pages": f.get("pages", 0),
                        "chunks": f.get("chunks", 0),
                        "total_ram_chunks": self.total_chunks,
                        "time_s": 0.0
                    }
        else:
            # If force re-indexing, remove old metadata and chunks for this doc
            self.ingested_files = [f for f in self.ingested_files if f.get("path") != abs_path and f.get("doc_name") != doc_base]
            keep_chunks = [c for c in self.bm25.chunks if c.doc_name != doc_base]
            if len(keep_chunks) < len(self.bm25.chunks):
                self.bm25.clear()
                self.vector_index.clear()
                if keep_chunks:
                    chunk_texts = [c.text for c in keep_chunks]
                    vecs = self.embedding_engine.embed_documents(chunk_texts)
                    self.bm25.add_chunks(keep_chunks)
                    self.vector_index.add_vectors(vecs, keep_chunks)
                self.total_chunks = len(keep_chunks)

        t0 = time.time()
        # 1. Vision & Multimodal Extraction (Formulas, Tables, Figures, Prose)
        doc_info = self.vision_extractor.extract_document(pdf_path, extract_figures=True)

        # 2. Semantic Chunking for prose text
        prose_chunks = chunk_document(
            doc_info=doc_info,
            chunk_size_words=self.config.chunk_size_words,
            chunk_overlap_words=self.config.chunk_overlap_words,
            min_chunk_words=self.config.min_chunk_words
        )

        special_chunks = doc_info.get("special_chunks", [])
        new_chunks = prose_chunks + special_chunks

        if not new_chunks:
            return {"status": "empty", "chunks": 0, "time_s": round(time.time() - t0, 3)}

        # 3. CPU Vectorization
        chunk_texts = [c.text for c in new_chunks]
        vectors = self.embedding_engine.embed_documents(chunk_texts)

        # 4. In-RAM Index Updating
        self.bm25.add_chunks(new_chunks)
        self.vector_index.add_vectors(vectors, new_chunks)
        self.graph_engine.index_chunks(new_chunks)

        self.total_chunks += len(new_chunks)
        self.ingested_files.append({
            "doc_name": doc_info["doc_name"],
            "path": doc_info["file_path"],
            "pages": doc_info["page_count"],
            "size_mb": doc_info["file_size_mb"],
            "chunks": len(new_chunks),
            "prose_chunks": len(prose_chunks),
            "special_chunks": len(special_chunks)
        })

        elapsed = round(time.time() - t0, 3)
        if auto_save:
            self.save_index()

        return {
            "status": "success",
            "doc_name": doc_info["doc_name"],
            "pages": doc_info["page_count"],
            "chunks": len(new_chunks),
            "prose_chunks": len(prose_chunks),
            "special_chunks": len(special_chunks),
            "total_ram_chunks": self.total_chunks,
            "time_s": elapsed
        }

    def ingest_directory(self, dir_path: str, max_files: Optional[int] = None) -> List[Dict[str, Any]]:
        """Scan directory recursively and ingest all scientific PDF files."""
        results = []
        count = 0
        for root, _, files in os.walk(dir_path):
            for f in files:
                if f.lower().endswith('.pdf'):
                    full_path = os.path.join(root, f)
                    res = self.ingest_pdf(full_path, auto_save=False)
                    results.append(res)
                    count += 1
                    if max_files and count >= max_files:
                        self.save_index()
                        return results
        # Persist index cache once after all files are processed
        self.save_index()
        return results

    def ingest_video(
        self,
        video_path: str,
        interval_seconds: float = 15.0,
        force: bool = False,
        auto_save: bool = True
    ) -> Dict[str, Any]:
        """
        Dynamically ingest a scientific video file:
        FFprobe metadata -> Keyframe extraction -> Audio track separation -> Audio transcription (Whisper) ->
        Unified timeline chunks -> CPU embedding -> In-RAM BM25 & FAISS indexing.
        """
        abs_path = os.path.abspath(video_path)
        doc_name = os.path.basename(video_path)
        if not force:
            for f in self.ingested_files:
                if f.get("path") == abs_path or f.get("doc_name") == doc_name:
                    return {
                        "status": "already_indexed",
                        "doc_name": doc_name,
                        "type": "video",
                        "chunks": f.get("chunks", 0),
                        "total_ram_chunks": self.total_chunks,
                        "time_s": 0.0
                    }
        t0 = time.time()
        # 1. Video Probe & Keyframe Timeline
        evidence_chunks = self.video_processor.build_video_evidence_chunks(video_path, interval_seconds=interval_seconds)

        # 2. Extract & Transcribe Audio (if audio track exists)
        audio_wav = self.video_processor.extract_audio(video_path)
        if audio_wav:
            audio_chunks = self.audio_processor.build_audio_evidence_chunks(audio_wav)
            for ac in audio_chunks:
                ac.source_name = doc_name
            evidence_chunks.extend(audio_chunks)

        if not evidence_chunks:
            return {"status": "empty", "doc_name": doc_name, "chunks": 0, "time_s": round(time.time() - t0, 3)}

        # 3. Convert to DocumentChunks
        new_doc_chunks = [c.to_document_chunk() for c in evidence_chunks]

        # 4. CPU Vectorization & In-RAM Indexing
        chunk_texts = [c.text for c in new_doc_chunks]
        vectors = self.embedding_engine.embed_documents(chunk_texts)

        self.bm25.add_chunks(new_doc_chunks)
        self.vector_index.add_vectors(vectors, new_doc_chunks)
        self.graph_engine.index_chunks(new_doc_chunks)

        self.total_chunks += len(new_doc_chunks)
        meta = self.video_processor.probe(video_path)
        self.ingested_files.append({
            "doc_name": doc_name,
            "path": abs_path,
            "type": "video",
            "duration": meta.get("duration_formatted", ""),
            "resolution": meta.get("resolution", ""),
            "chunks": len(new_doc_chunks)
        })

        elapsed = round(time.time() - t0, 3)
        if auto_save:
            self.save_index()

        return {
            "status": "success",
            "doc_name": doc_name,
            "type": "video",
            "chunks": len(new_doc_chunks),
            "total_ram_chunks": self.total_chunks,
            "time_s": elapsed
        }

    def ingest_audio(
        self,
        audio_path: str,
        force: bool = False,
        auto_save: bool = True
    ) -> Dict[str, Any]:
        """
        Dynamically ingest a spoken research audio file:
        Local Faster-Whisper transcription -> Timestamped speaker segments ->
        Unified audio evidence chunks -> CPU embedding -> In-RAM BM25 & FAISS indexing.
        """
        abs_path = os.path.abspath(audio_path)
        doc_name = os.path.basename(audio_path)
        if not force:
            for f in self.ingested_files:
                if f.get("path") == abs_path or f.get("doc_name") == doc_name:
                    return {
                        "status": "already_indexed",
                        "doc_name": doc_name,
                        "type": "audio",
                        "chunks": f.get("chunks", 0),
                        "total_ram_chunks": self.total_chunks,
                        "time_s": 0.0
                    }
        t0 = time.time()
        # 1. Transcribe & Segment
        segments = self.audio_processor.transcribe(audio_path)
        if not segments:
            return {"status": "empty", "doc_name": doc_name, "chunks": 0, "time_s": round(time.time() - t0, 3)}

        # 2. Build Audio Evidence Chunks
        evidence_chunks = self.audio_processor.build_audio_evidence_chunks(audio_path, segments=segments)
        new_doc_chunks = [c.to_document_chunk() for c in evidence_chunks]

        # 3. CPU Vectorization & Indexing
        chunk_texts = [c.text for c in new_doc_chunks]
        vectors = self.embedding_engine.embed_documents(chunk_texts)

        self.bm25.add_chunks(new_doc_chunks)
        self.vector_index.add_vectors(vectors, new_doc_chunks)
        self.graph_engine.index_chunks(new_doc_chunks)

        self.total_chunks += len(new_doc_chunks)
        self.ingested_files.append({
            "doc_name": doc_name,
            "path": abs_path,
            "type": "audio",
            "segments": len(segments),
            "chunks": len(new_doc_chunks)
        })

        elapsed = round(time.time() - t0, 3)
        if auto_save:
            self.save_index()

        return {
            "status": "success",
            "doc_name": doc_name,
            "type": "audio",
            "chunks": len(new_doc_chunks),
            "total_ram_chunks": self.total_chunks,
            "time_s": elapsed
        }

    def process_meeting(
        self,
        audio_path: str,
        title: str = "Research Lab Meeting",
        auto_save: bool = True
    ) -> Dict[str, Any]:
        """
        End-to-end Academic Meeting Intelligence:
        Transcribe -> Diarize speaker turns -> Extract consensus decisions, hypotheses, and action items ->
        Generate Laboratory Memo artifact -> Index transcript into RAM hybrid retriever.
        """
        ingest_res = self.ingest_audio(audio_path, auto_save=auto_save)
        raw_segs = self.audio_processor.transcribe(audio_path)
        diarized = self.meeting_engine.diarize_segments(raw_segs)
        insights = self.meeting_engine.extract_meeting_insights(diarized, title=title)
        memo_md = self.meeting_engine.format_meeting_markdown(insights)

        from privearch.schemas import ArtifactType
        doc_name = os.path.basename(audio_path)
        artifact = self.artifact_registry.register_artifact(
            name=f"Meeting Memo: {title}",
            artifact_type=ArtifactType.MARKDOWN_REPORT,
            content=memo_md,
            provenance={"source_doc": doc_name, "meeting_title": title, "speakers": insights["speakers"]},
            description=f"Automated meeting intelligence memo with decisions and action items for {title}."
        )

        return {
            "status": "success",
            "title": title,
            "artifact_id": artifact.artifact_id,
            "insights": insights,
            "markdown_memo": memo_md,
            "chunks_indexed": ingest_res.get("chunks", 0)
        }

    def ingest_media(
        self,
        media_path: str,
        force: bool = False,
        auto_save: bool = True
    ) -> Dict[str, Any]:
        """
        Universal Multimodal Dropzone Ingestor:
        Routes PDFs, Videos, Audio recordings, and Transcripts to the appropriate ingestion engine.
        """
        ext = os.path.splitext(media_path)[1].lower()
        if ext == ".pdf":
            return self.ingest_pdf(media_path, force=force, auto_save=auto_save)
        elif ext in (".mp4", ".mkv", ".mov", ".avi", ".webm"):
            return self.ingest_video(media_path, force=force, auto_save=auto_save)
        elif ext in (".wav", ".mp3", ".m4a", ".flac", ".ogg", ".vtt", ".srt"):
            return self.ingest_audio(media_path, force=force, auto_save=auto_save)
        else:
            return {
                "status": "unsupported",
                "doc_name": os.path.basename(media_path),
                "error": f"Unsupported media format: {ext}"
            }

    def execute_rlcd(self, query: str, deep_thinking: bool = True) -> PrivearchReport:
        """
        Executes the full RLCD 4-Stage Operating System Pipeline with Phase 2 Scientific Compute:
          Stage 1: Query Analyzer (0.5B Router)
          Stage 2: Hybrid RRF Retriever (BM25 + FAISS)
          Phase 2 Compute: Deterministic SymPy/NumPy Solver & Artifact Generation
          Stage 3: Synthesis Engine (4B Model with R1 / CoT Reasoning & Ground Truth Injection)
          Stage 4: Adversarial Verifier (0.5B Model + Deterministic Math Audit)
        """
        t_start = time.time()
        stage_timings: Dict[str, float] = {}

        # --- Stage 1: Router (0.5B) ---
        t1 = time.time()
        analysis = self.router.analyze(query)
        stage_timings["router_ms"] = round((time.time() - t1) * 1000, 1)

        # --- Stage 2: Logic (Hybrid RRF Retriever) ---
        t2 = time.time()
        retrieved_chunks = self.hybrid_retriever.retrieve(
            query=query,
            lexical_keywords=analysis.lexical_keywords,
            top_k_bm25=self.config.top_k_bm25,
            top_k_dense=self.config.top_k_dense,
            top_k_final=self.config.top_k_final
        )
        stage_timings["retrieval_ms"] = round((time.time() - t2) * 1000, 1)

        # --- GraphRAG Multi-Hop Knowledge & Cross-Document Citation Expansion ---
        t_graph = time.time()
        graph_subnetwork = self.graph_engine.query_subgraph(query=query, top_k_entities=6, depth=2)
        graph_expanded_chunks = self.graph_engine.expand_retrieval(
            query=query,
            retrieved_chunks=retrieved_chunks,
            all_chunks=self.bm25.chunks,
            max_expansion=2
        )
        for extra_chunk in graph_expanded_chunks:
            retrieved_chunks.append(ScoredChunk(
                chunk=extra_chunk,
                rrf_score=0.015,
                final_rank=len(retrieved_chunks) + 1
            ))
        stage_timings["graph_ms"] = round((time.time() - t_graph) * 1000, 1)

        # --- Phase 2: Deterministic Scientific Computation (Non-LLM Truth) ---
        t_calc = time.time()
        calculations: List[CalculationVerification] = []
        artifacts: List[ArtifactRecord] = []
        tool_executions: List[ToolCallResult] = []
        injected_calc_context = ""

        is_calc_task = (analysis.task_type == TaskType.CALCULATION_DERIVATION)
        equations = EquationParser.extract_equations(query)
        variables = EquationParser.extract_variable_assignments(query)

        # If equation not in query, check top retrieved chunks
        if not equations and retrieved_chunks:
            for sc in retrieved_chunks[:3]:
                found_eqs = EquationParser.extract_equations(sc.chunk.text)
                if found_eqs:
                    equations.extend(found_eqs)
                    break

        # If variables not in query, check top retrieved chunks
        if not variables and retrieved_chunks:
            for sc in retrieved_chunks[:3]:
                found_vars = EquationParser.extract_variable_assignments(sc.chunk.text)
                if found_vars:
                    variables.update(found_vars)

        target_eq = equations[0] if equations else ""
        target_var = "ans"
        if target_eq and (variables or is_calc_task):
            for ent in analysis.key_entities:
                if len(ent) <= 4 and ent.isalnum():
                    target_var = ent
                    break
            if target_var == "ans" and "=" in target_eq:
                lhs = target_eq.split("=")[0].strip()
                if len(lhs) <= 4 and lhs.isalnum():
                    target_var = lhs

            calc_val, formula_str, derivation_code = self.solver.solve_equation(
                equation_str=target_eq,
                target_variable=target_var,
                known_values=variables
            )

            if calc_val is not None:
                tool_executions.append(ToolCallResult(
                    tool_name="deterministic_solver",
                    success=True,
                    output=calc_val,
                    stdout=formula_str,
                    execution_time_ms=round((time.time() - t_calc) * 1000, 1),
                    metadata={"target_variable": target_var, "equation": target_eq}
                ))

                source_doc = retrieved_chunks[0].chunk.doc_name if retrieved_chunks else "User Query"
                source_page = retrieved_chunks[0].chunk.page_num if retrieved_chunks else None

                calc_artifact = self.artifact_registry.save_calculation(
                    name=f"Calculation of {target_var}",
                    equation=target_eq,
                    variables=variables,
                    computed_value=calc_val,
                    code_executed=derivation_code,
                    source_doc=source_doc,
                    source_page=source_page,
                    description=f"Deterministic SymPy calculation for {target_var} in '{target_eq}'"
                )
                artifacts.append(calc_artifact)

                injected_calc_context = (
                    f"\n\n[DETERMINISTIC SCIENTIFIC COMPUTATION - VERIFIED TRUTH]:\n"
                    f"Equation: {target_eq}\n"
                    f"Parameters: {variables}\n"
                    f"Symbolic Formulation: {formula_str}\n"
                    f"Deterministic Computed Value: {calc_val:.5g}\n"
                    f"CRITICAL: Use this EXACT computed value in your synthesis.\n"
                )

        stage_timings["compute_ms"] = round((time.time() - t_calc) * 1000, 1)

        # --- Stage 3: Control (4B Synthesis Engine with R1 / CoT Reasoning) ---
        t3 = time.time()
        augmented_analysis = analysis.model_copy()
        if injected_calc_context:
            augmented_analysis.analysis_rationale = (
                f"{analysis.analysis_rationale} {injected_calc_context}"
            )

        synth_output = self.synthesis.synthesize(
            query=query,
            query_analysis=augmented_analysis,
            retrieved_chunks=retrieved_chunks,
            injected_calc_context=injected_calc_context,
            deep_thinking=deep_thinking
        )
        raw_synthesis = synth_output.text
        thought_trace = synth_output.thought_trace
        reasoning_steps = synth_output.reasoning_steps
        thinking_duration_s = synth_output.duration_s
        stage_timings["synthesis_ms"] = round((time.time() - t3) * 1000, 1)

        # --- Audit Calculations Deterministically ---
        if target_eq and variables:
            calc_audit = self.solver.verify_calculation(
                equation_str=target_eq,
                target_variable=target_var,
                known_values=variables,
                model_claimed_text=raw_synthesis
            )
            calculations.append(calc_audit)

        # --- Stage 4: Decision (0.5B Adversarial Verifier) ---
        t4 = time.time()
        audit, annotated_synthesis = self.verifier.audit(
            synthesis_text=raw_synthesis,
            retrieved_chunks=retrieved_chunks,
            calculation_audits=calculations
        )
        stage_timings["verifier_ms"] = round((time.time() - t4) * 1000, 1)

        total_time_ms = round((time.time() - t_start) * 1000, 1)

        # System telemetry
        mem_info = psutil.virtual_memory()
        stats = {
            "total_elapsed_ms": total_time_ms,
            "stage_timings": stage_timings,
            "models_used": {
                "router_0_5b": self.router_model,
                "synthesis_4b": self.synthesis_model,
                "verifier_0_5b": self.verifier_model
            },
            "ram_used_percent": mem_info.percent,
            "ram_available_gb": round(mem_info.available / (1024**3), 2),
            "total_indexed_chunks": self.total_chunks,
            "total_indexed_docs": len(self.ingested_files),
            "total_artifacts": len(self.artifact_registry.list_all()),
            "deep_thinking_enabled": deep_thinking,
            "thinking_duration_s": thinking_duration_s,
            "graph_nodes": len(graph_subnetwork.nodes),
            "graph_edges": len(graph_subnetwork.edges),
            "cross_document_bridges": len(graph_subnetwork.bridges)
        }

        return PrivearchReport(
            query=query,
            query_analysis=analysis,
            retrieved_chunks=retrieved_chunks,
            raw_synthesis=raw_synthesis,
            verification=audit,
            annotated_synthesis=annotated_synthesis,
            execution_stats=stats,
            calculations=calculations,
            artifacts=artifacts,
            tool_executions=tool_executions,
            reasoning_trace=thought_trace,
            reasoning_steps=reasoning_steps,
            thinking_duration_s=thinking_duration_s,
            deep_thinking_enabled=deep_thinking,
            graph_subnetwork=graph_subnetwork
        )

    def get_system_status(self) -> Dict[str, Any]:
        """Telemetry snapshot of Privearch OS."""
        mem = psutil.virtual_memory()
        return {
            "version": "1.1.0",
            "airgap_mode": self.config.zero_trust_airgap,
            "indexed_documents": len(self.ingested_files),
            "indexed_chunks": self.total_chunks,
            "registered_tools": [t["name"] for t in self.tool_graph.list_tools()],
            "total_artifacts": len(self.artifact_registry.list_all()),
            "router_model": self.router_model,
            "synthesis_model": self.synthesis_model,
            "verifier_model": self.verifier_model,
            "embedding_engine": self.config.embedding_backend,
            "host_ram_used_percent": mem.percent,
            "host_ram_free_gb": round(mem.available / (1024**3), 2),
            "graph_nodes": self.graph_engine.graph.number_of_nodes(),
            "graph_edges": self.graph_engine.graph.number_of_edges(),
            "cross_document_bridges": len(self.graph_engine.bridges),
            "communities_count": len(self.graph_engine.communities)
        }

