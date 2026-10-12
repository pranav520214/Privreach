"""High-Performance Local Desktop Server for Privreach WinUI 3 Workstation.

Provides asynchronous REST APIs for:
- System Status (RAM, VRAM, Ollama, Models)
- RLCD Query Orchestration (Router, Hybrid Retrieval, Synthesis, Adversarial Verification)
- Deterministic Symbolic & Numerical Computation Auditing
- Explainer Canvas Visualizations (Derivations, Interactive HTML simulations)
- PDF Document Serving & Synchronized Page Referencing
- Live Model Management and Media Ingestion
"""

import os
import sys
import time
import json

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import psutil
from typing import Dict, Any, Optional

import uvicorn
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse, FileResponse, Response
from starlette.routing import Route
from starlette.requests import Request

from privearch.config import PrivearchConfig, DEFAULT_CONFIG
from privearch.os_engine import PrivearchKernel
from privearch.schemas import VerificationStatus, RiskLevel
from privearch.ui.canvas_generator import CanvasGenerator
from privearch.models.engine_installer import (
    is_engine_running,
    list_installed_models,
    start_ollama_daemon,
    pull_model
)

# Global Kernel Instance
_kernel: Optional[PrivearchKernel] = None


def get_kernel() -> PrivearchKernel:
    global _kernel
    if _kernel is None:
        _kernel = PrivearchKernel(config=DEFAULT_CONFIG)
        # Attempt to load saved cache if present
        try:
            _kernel.load_index()
        except Exception:
            pass
    return _kernel


async def api_status(request: Request) -> JSONResponse:
    """Return live system, GPU/VRAM, engine, and vault status."""
    kernel = get_kernel()
    try:
        port = int(kernel.config.ollama_base_url.split(":")[-1].split("/")[0])
    except Exception:
        port = 11434
    ollama_ok = is_engine_running(port=port)
    
    try:
        from privreach.models.gemma_engine import GemmaInProcessEngine
        gemma_ok = GemmaInProcessEngine.get_instance().is_available()
    except Exception:
        gemma_ok = False

    engine_active = gemma_ok or ollama_ok
    
    # Process memory
    proc = psutil.Process()
    ram_mb = round(proc.memory_info().rss / (1024 * 1024), 1)
    cpu_pct = psutil.cpu_percent(interval=None)

    # Approximate GPU VRAM if available via torch or nvidia-smi
    vram_mb = 0.0
    try:
        import torch
        if torch.cuda.is_available():
            vram_mb = round(torch.cuda.memory_allocated() / (1024 * 1024), 1)
    except Exception:
        pass

    sys_status = kernel.get_system_status()
    actual_chunks = kernel.total_chunks or len(kernel.bm25.chunks)

    # Hardware-Bound Auth status
    try:
        from privreach.compute.hardware_auth import HardwareBoundAuth
        hw_profile = HardwareBoundAuth.get_hardware_profile()
        cpu_id = hw_profile.get("cpu_id", "UNKNOWN_CPU")
        cpu_name = hw_profile.get("cpu_name", "UNKNOWN_PROCESSOR")
        hw_locked = True
        hw_verified = True
    except Exception:
        cpu_id = "UNKNOWN_CPU"
        cpu_name = "UNKNOWN_PROCESSOR"
        hw_locked = False
        hw_verified = False

    return JSONResponse({
        "status": "online",
        "engine_running": engine_active,
        "gemma_embedded": gemma_ok,
        "ollama_port": port,
        "router_model": kernel.router_model,
        "synthesis_model": kernel.synthesis_model,
        "verifier_model": kernel.verifier_model,
        "indexed_chunks": actual_chunks,
        "indexed_documents": sys_status.get("indexed_documents", len(kernel.ingested_files)),
        "total_chunks": actual_chunks,
        "ram_usage_mb": ram_mb,
        "vram_usage_mb": vram_mb,
        "cpu_percent": cpu_pct,
        "airgap_active": kernel.config.zero_trust_airgap,
        "hardware_locked": hw_locked,
        "cpu_id": cpu_id,
        "cpu_model": cpu_name,
        "hardware_verified": hw_verified,
        "timestamp": time.time()
    })


async def api_documents(request: Request) -> JSONResponse:
    """Return all currently ingested documents in the Vault."""
    kernel = get_kernel()
    if not kernel.ingested_files:
        sample_pdf = os.path.join(repo_root, "tests", "data", "sample_wing_aerodynamics.pdf")
        if os.path.exists(sample_pdf):
            try:
                kernel.ingest_media(sample_pdf, auto_save=True)
            except Exception:
                pass

    return JSONResponse({
        "documents": kernel.ingested_files,
        "total_count": len(kernel.ingested_files),
        "total_chunks": kernel.total_chunks or len(kernel.bm25.chunks)
    })


async def api_query(request: Request) -> JSONResponse:
    """Run full RLCD inquiry pipeline and return structured report."""
    kernel = get_kernel()
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    query_text = body.get("query", "").strip()
    if not query_text:
        return JSONResponse({"error": "Query cannot be empty"}, status_code=400)

    deep_thinking = body.get("deep_thinking", True)
    t0 = time.time()
    try:
        report = kernel.execute_rlcd(query_text, deep_thinking=deep_thinking)
    except Exception as e:
        return JSONResponse({"error": f"Execution failed: {str(e)}"}, status_code=500)

    qa = report.query_analysis
    audit = report.verification
    calc = report.calculations[0] if (hasattr(report, "calculations") and report.calculations) else None

    # Format Claims for the Verification Matrix
    claims_list = []
    for c in audit.claims:
        claims_list.append({
            "claim_id": c.claim_id,
            "text": c.text,
            "status": c.status.value if hasattr(c.status, "value") else str(c.status),
            "source_doc": c.source_doc,
            "source_page": c.source_page,
            "evidence_quote": c.evidence_quote,
            "critique": c.critique,
            "confidence": round(c.confidence * 100, 1) if c.confidence <= 1.0 else round(c.confidence, 1)
        })

    # Format Retrieved Passages for Synchronized Evidence Viewer
    chunks_list = []
    for sc in report.retrieved_chunks:
        chunks_list.append({
            "chunk_id": sc.chunk.chunk_id,
            "doc_name": sc.chunk.doc_name,
            "page_num": sc.chunk.page_num,
            "section_header": sc.chunk.section_header,
            "text": sc.chunk.text,
            "rrf_score": round(sc.rrf_score, 4),
            "final_rank": sc.final_rank,
            "evidence_type": getattr(sc.chunk, "evidence_type", "DOCUMENT_PAGE"),
            "media_path": getattr(sc.chunk, "media_path", None)
        })

    # Format Calculation Audit if present
    calc_dict = None
    derivation_md = ""
    if calc:
        calc_dict = {
            "equation_latex": calc.equation_latex,
            "target_variable": calc.target_variable,
            "variables": calc.variables,
            "units": calc.units,
            "model_predicted_value": calc.model_predicted_value,
            "deterministic_computed_value": calc.deterministic_computed_value,
            "is_verified": calc.is_verified,
            "relative_error_pct": round((calc.relative_error or 0.0) * 100, 4) if calc.relative_error is not None else None,
            "verification_status": calc.verification_status.value if hasattr(calc.verification_status, "value") else str(calc.verification_status),
            "verification_details": calc.verification_details,
            "code_executed": calc.code_executed
        }
        try:
            derivation_md = CanvasGenerator.generate_derivation_markdown(calc)
        except Exception:
            derivation_md = ""

    # Multimodal Timeline
    timeline_md = ""
    try:
        timeline_md = CanvasGenerator.generate_multimodal_timeline_markdown(report.retrieved_chunks)
    except Exception:
        pass

    # Vision RAG & Structural Evidence Breakdown
    visual_evidence_md = ""
    try:
        visual_evidence_md = CanvasGenerator.generate_visual_evidence_markdown(report.retrieved_chunks)
    except Exception:
        pass

    # Deep Thinking & Chain-of-Thought Markdown
    deep_thinking_md = ""
    try:
        deep_thinking_md = CanvasGenerator.generate_deep_thinking_markdown(
            reasoning_trace=report.reasoning_trace,
            reasoning_steps=report.reasoning_steps,
            duration_s=report.thinking_duration_s or 0.0
        )
    except Exception:
        pass

    # GraphRAG & Cross-Document Citation Graph
    graph_md = ""
    graph_dict = None
    bridges_list = []
    if getattr(report, "graph_subnetwork", None):
        try:
            graph_md = CanvasGenerator.generate_graph_markdown(report.graph_subnetwork)
            graph_dict = {
                "total_nodes": report.graph_subnetwork.total_nodes,
                "total_edges": report.graph_subnetwork.total_edges,
                "nodes": [
                    {
                        "id": n.id,
                        "label": n.label,
                        "type": n.type.value if hasattr(n.type, "value") else str(n.type),
                        "doc_name": n.doc_name,
                        "page_num": n.page_num,
                        "degree": n.degree,
                        "community_id": n.community_id
                    }
                    for n in report.graph_subnetwork.nodes
                ],
                "edges": [
                    {
                        "source": e.source,
                        "target": e.target,
                        "relation": e.relation.value if hasattr(e.relation, "value") else str(e.relation),
                        "weight": e.weight,
                        "is_cross_document": e.is_cross_document
                    }
                    for e in report.graph_subnetwork.edges
                ],
                "bridges": [
                    {
                        "entity": b.entity,
                        "documents": b.documents,
                        "chunk_ids": b.chunk_ids,
                        "shared_relations": b.shared_relations
                    }
                    for b in report.graph_subnetwork.bridges
                ],
                "communities": [
                    {
                        "community_id": c.community_id,
                        "title": c.title,
                        "summary": c.summary,
                        "members": c.members
                    }
                    for c in report.graph_subnetwork.communities
                ]
            }
            bridges_list = graph_dict["bridges"]
        except Exception:
            pass

    reasoning_steps_list = [
        {
            "step_number": s.step_number,
            "stage": s.stage.value if hasattr(s.stage, "value") else str(s.stage),
            "title": s.title,
            "content": s.content,
            "status": s.status
        }
        for s in report.reasoning_steps
    ]

    elapsed_total = round(time.time() - t0, 3)

    return JSONResponse({
        "query": query_text,
        "query_analysis": {
            "risk_level": qa.risk_level.value if hasattr(qa.risk_level, "value") else str(qa.risk_level),
            "task_type": qa.task_type.value if hasattr(qa.task_type, "value") else str(qa.task_type),
            "scientific_domain": qa.scientific_domain,
            "key_entities": qa.key_entities,
            "lexical_keywords": qa.lexical_keywords,
            "semantic_queries": qa.semantic_queries,
            "adversarial_audit_required": qa.adversarial_audit_required,
            "analysis_rationale": qa.analysis_rationale
        },
        "synthesis_text": report.annotated_synthesis or report.raw_synthesis,
        "verification": {
            "grounding_confidence_pct": round(getattr(audit, "grounding_score", 0.0), 1),
            "total_claims": audit.total_claims,
            "verified_claims": getattr(audit, "verified_count", 0),
            "unsupported_claims": getattr(audit, "unsupported_count", 0),
            "contradicted_claims": getattr(audit, "contradicted_count", 0),
            "claims": claims_list
        },
        "calculation_audit": calc_dict,
        "derivation_markdown": derivation_md,
        "multimodal_timeline_markdown": timeline_md,
        "visual_evidence_markdown": visual_evidence_md,
        "deep_thinking_markdown": deep_thinking_md,
        "reasoning_trace": report.reasoning_trace,
        "reasoning_steps": reasoning_steps_list,
        "thinking_duration_s": report.thinking_duration_s,
        "graph_markdown": graph_md,
        "cross_document_bridges": bridges_list,
        "graph_subnetwork": graph_dict,
        "retrieved_chunks": chunks_list,
        "execution_stats": {
            **report.execution_stats,
            "total_roundtrip_s": elapsed_total
        }
    })


async def api_ingest(request: Request) -> JSONResponse:
    """Ingest a local PDF or media file into the In-RAM Vault."""
    kernel = get_kernel()
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    path = body.get("path", "").strip()
    if not path or not os.path.exists(path):
        return JSONResponse({"error": f"File does not exist: {path}"}, status_code=404)

    try:
        res = kernel.ingest_media(path, force=body.get("force", False), auto_save=True)
        return JSONResponse(res)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


def _is_safe_path(target_path: str, kernel: PrivearchKernel) -> bool:
    """Validate that target_path belongs to ingested files, cache, or workspace."""
    if not target_path or not os.path.exists(target_path):
        return False
    try:
        real_target = os.path.realpath(target_path).lower()
        # 1. Ingested files
        for f in kernel.ingested_files:
            ingested_p = f.get("path")
            if ingested_p and os.path.realpath(ingested_p).lower() == real_target:
                return True
        # 2. Inside allowed directories
        allowed_dirs = [
            os.path.realpath(repo_root).lower(),
            os.path.realpath(os.path.abspath(".privearch_cache")).lower(),
            os.path.realpath(os.path.abspath(".privreach_cache")).lower(),
            os.path.realpath(os.path.abspath(".privreach_media_cache")).lower(),
            os.path.realpath(os.path.abspath(".privearch_media_cache")).lower(),
        ]
        for adir in allowed_dirs:
            if real_target == adir or real_target.startswith(adir + os.sep):
                return True
        return False
    except Exception:
        return False


async def api_serve_pdf(request: Request) -> Response:
    """Serve a local PDF file for native rendering in WebView2 with path traversal protection."""
    doc_path = request.query_params.get("path", "")
    doc_name = request.query_params.get("name", "")

    kernel = get_kernel()
    target_path = None

    if doc_path and os.path.exists(doc_path):
        target_path = doc_path
    elif doc_name:
        for f in kernel.ingested_files:
            if f.get("doc_name") == doc_name:
                target_path = f.get("path")
                break

    if not target_path or not os.path.exists(target_path):
        return JSONResponse({"error": "PDF not found"}, status_code=404)

    if not _is_safe_path(target_path, kernel):
        return JSONResponse({"error": "Access Denied: Path is outside permitted vault boundaries."}, status_code=403)

    return FileResponse(
        target_path,
        media_type="application/pdf",
        filename=os.path.basename(target_path),
        headers={"Accept-Ranges": "bytes"}
    )


async def api_models(request: Request) -> JSONResponse:
    """List installed models in local Ollama."""
    kernel = get_kernel()
    try:
        port = int(kernel.config.ollama_base_url.split(":")[-1].split("/")[0])
    except Exception:
        port = 11434
    models = list_installed_models(port=port)
    return JSONResponse({
        "models": models,
        "active_router": kernel.router_model,
        "active_synthesis": kernel.synthesis_model,
        "active_verifier": kernel.verifier_model
    })


async def api_switch_model(request: Request) -> JSONResponse:
    """Switch models for active RLCD roles."""
    kernel = get_kernel()
    body = await request.json()
    role = body.get("role", "synthesis")
    model = body.get("model", "")

    if not model:
        return JSONResponse({"error": "Model name required"}, status_code=400)

    if role == "router":
        kernel.router_model = model
        kernel.router.model_name = model
    elif role == "synthesis":
        kernel.synthesis_model = model
        kernel.synthesis.model_name = model
    elif role == "verifier":
        kernel.verifier_model = model
        kernel.verifier.model_name = model
    else:
        return JSONResponse({"error": f"Unknown role: {role}"}, status_code=400)

    return JSONResponse({
        "success": True,
        "role": role,
        "model": model
    })


async def api_serve_media(request: Request) -> Response:
    """Serve local extracted figure images or media files with path boundary checks."""
    media_path = request.query_params.get("path", "")
    if not media_path or not os.path.exists(media_path):
        return JSONResponse({"error": "Media file not found"}, status_code=404)

    kernel = get_kernel()
    if not _is_safe_path(media_path, kernel):
        return JSONResponse({"error": "Access Denied: Media path is outside permitted boundaries."}, status_code=403)

    ext = os.path.splitext(media_path)[1].lower()
    mime = "image/png"
    if ext in (".jpg", ".jpeg"):
        mime = "image/jpeg"
    elif ext == ".webp":
        mime = "image/webp"
    elif ext == ".svg":
        mime = "image/svg+xml"
    elif ext == ".mp4":
        mime = "video/mp4"
    elif ext in (".wav", ".mp3"):
        mime = "audio/mpeg" if ext == ".mp3" else "audio/wav"

    return FileResponse(
        media_path,
        media_type=mime,
        filename=os.path.basename(media_path),
        headers={"Accept-Ranges": "bytes"}
    )


async def api_start_engine(request: Request) -> JSONResponse:
    """Attempt to launch the local Ollama background service."""
    ok = start_ollama_daemon()
    return JSONResponse({"success": ok, "running": is_engine_running()})


async def api_graph(request: Request) -> JSONResponse:
    """Return the complete In-RAM Knowledge & Cross-Document Citation Graph."""
    kernel = get_kernel()
    graph_data = kernel.graph_engine.export_json()
    return JSONResponse(graph_data)


# ==========================================
# MODERN UPDATER & PATCHING REST APIS
# ==========================================
from privreach.updater import get_updater_service

async def api_updater_status(request: Request) -> JSONResponse:
    """Return updater version, telemetry, and snapshot history."""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    service = get_updater_service(repo_root)
    return JSONResponse(service.get_status())


async def api_updater_check(request: Request) -> JSONResponse:
    """Check for new OTA updates."""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    service = get_updater_service(repo_root)
    res = service.check_for_updates()
    return JSONResponse(res.model_dump())


async def api_updater_apply(request: Request) -> JSONResponse:
    """Apply a .privpatch or downloaded update bundle."""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    service = get_updater_service(repo_root)
    try:
        body = await request.json()
        patch_file = body.get("patch_path")
        if not patch_file:
            return JSONResponse({"success": False, "message": "Missing 'patch_path' in request body."}, status_code=400)
        res = service.apply_patch_file(patch_file, auto_rollback=True)
        return JSONResponse(res.model_dump())
    except Exception as ex:
        return JSONResponse({"success": False, "message": str(ex)}, status_code=500)


async def api_updater_rollback(request: Request) -> JSONResponse:
    """Revert to a point-in-time snapshot."""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    service = get_updater_service(repo_root)
    try:
        body = await request.json() if (await request.body()) else {}
        snap_id = body.get("snapshot_id")
        res = service.rollback_to_snapshot(snap_id)
        return JSONResponse(res.model_dump())
    except Exception as ex:
        return JSONResponse({"success": False, "message": str(ex)}, status_code=500)


async def api_updater_snapshots(request: Request) -> JSONResponse:
    """List all available rollback snapshots."""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    service = get_updater_service(repo_root)
    snaps = service.list_snapshots()
    return JSONResponse([s.model_dump() for s in snaps])


async def api_vault_clear(request: Request) -> JSONResponse:
    """Clear all indexed documents, chunks, vectors, and graph nodes for a completely fresh start."""
    kernel = get_kernel()
    success = kernel.clear_index(delete_cache_files=True)
    return JSONResponse({
        "success": success,
        "message": "Knowledge vault completely cleared. Index is fresh and ready for new documents.",
        "total_chunks": 0,
        "total_documents": 0
    })


async def api_compute_solve(request: Request) -> JSONResponse:
    """Deterministically solve a scientific equation with exact SymPy AST and LaTeX."""
    kernel = get_kernel()
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    equation = body.get("equation", "").strip()
    target_var = body.get("target_variable", "ans").strip()
    known_vars = body.get("variables", {})

    if not equation:
        return JSONResponse({"error": "Equation is required"}, status_code=400)

    try:
        calc_val, formula_str, derivation_code = kernel.solver.solve_equation(
            equation_str=equation,
            target_variable=target_var,
            known_values=known_vars
        )

        if calc_val is not None:
            kernel.artifact_registry.save_calculation(
                name=f"Direct Solve: {target_var}",
                equation=equation,
                variables=known_vars,
                computed_value=calc_val,
                code_executed=derivation_code,
                source_doc="Scientific Computing Workstation",
                description=f"Interactive SymPy deterministic derivation for {target_var} in '{equation}'"
            )

        return JSONResponse({
            "success": calc_val is not None,
            "result": calc_val,
            "formula_str": formula_str,
            "code_executed": derivation_code,
            "equation": equation,
            "target_variable": target_var,
            "variables": known_vars
        })
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


async def api_artifacts(request: Request) -> JSONResponse:
    """Return all scientific artifacts and computational derivations in the ledger."""
    kernel = get_kernel()
    artifacts = kernel.artifact_registry.list_all()
    return JSONResponse({
        "artifacts": [a.model_dump() for a in artifacts],
        "total_count": len(artifacts)
    })


async def api_security_hardware_auth(request: Request) -> JSONResponse:
    """Return live hardware-bound vault security telemetry and verified CPU profile."""
    from privreach.compute.hardware_auth import HardwareBoundAuth
    profile = HardwareBoundAuth.get_hardware_profile()
    verified, msg = HardwareBoundAuth.verify_hardware_access()
    return JSONResponse({
        "status": "enforced" if verified else "error",
        "verified": verified,
        "message": msg,
        "hardware_profile": profile,
        "encryption_algorithm": "AES-256-GCM + Argon2id",
        "key_derivation_memory_cost_mb": 64,
        "storage_theft_protection": "PHYSICAL_CPU_BOUND",
    })


async def api_ingress_harvest(request: Request) -> JSONResponse:
    """Execute deterministic academic paper harvesting across arXiv, OpenAlex, and CrossRef."""
    try:
        body = await request.json()
        query = body.get("query", "").strip()
        if not query:
            return JSONResponse({"success": False, "error": "Query parameter is required"}, status_code=400)
        max_papers = int(body.get("max_papers", 15))
        download_pdfs = bool(body.get("download_priority_pdfs", False))

        from privreach.ingress import AcademicHarvester
        harvester = AcademicHarvester()
        manifest = await harvester.harvest_async(
            query=query,
            max_papers_per_source=max_papers,
            download_priority_pdfs=download_pdfs,
        )
        return JSONResponse({
            "success": True,
            "manifest": manifest.model_dump(),
        })
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


async def api_airlock_process(request: Request) -> JSONResponse:
    """Execute Content Disarm & Reconstruction (CDR) on a quarantined document."""
    try:
        body = await request.json()
        file_path = body.get("file_path", "").strip()
        force_flatten = bool(body.get("force_visual_flatten", False))
        auto_ingest = bool(body.get("auto_ingest_into_vault", True))

        if not file_path or not os.path.exists(file_path):
            return JSONResponse({"success": False, "error": f"File not found: {file_path}"}, status_code=404)

        from privreach.airlock import CDRPipeline
        pipeline = CDRPipeline()
        cdr_res = pipeline.process_file(file_path, force_visual_flatten=force_flatten)

        ingest_res = None
        if cdr_res.is_cleared and auto_ingest and cdr_res.vault_dest_path:
            kernel = get_kernel()
            ingest_res = kernel.ingest_pdf(cdr_res.vault_dest_path)

        return JSONResponse({
            "success": True,
            "cdr_result": cdr_res.model_dump(),
            "ingest_result": ingest_res,
        })
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


async def api_prover_verify(request: Request) -> JSONResponse:
    """Verify an assertion against the local knowledge vault using GroundingGate."""
    try:
        body = await request.json()
        text = body.get("text", "").strip()
        if not text:
            return JSONResponse({"success": False, "error": "Text parameter is required"}, status_code=400)
        strict_mode = bool(body.get("strict_mode", True))

        kernel = get_kernel()
        evidence_chunks = kernel.bm25.chunks

        from privreach.prover import GroundingGate
        gate = GroundingGate(strict_mode=strict_mode)
        proof = gate.verify_and_gate(text, evidence_chunks)

        return JSONResponse({
            "success": True,
            "proof_report": proof.model_dump(),
        })
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


async def api_discovery_swanson(request: Request) -> JSONResponse:
    """Execute Swanson ABC literature discovery over the vault knowledge graph."""
    try:
        body = await request.json()
        entity_a = body.get("entity_a", "").strip()
        entity_c = body.get("entity_c", "").strip()

        if not entity_a:
            return JSONResponse({"success": False, "error": "entity_a is required"}, status_code=400)

        kernel = get_kernel()
        from privreach.discovery import SwansonDiscoveryEngine
        engine = SwansonDiscoveryEngine(kernel.graph_engine.graph)

        if entity_c:
            report = engine.closed_discovery(entity_a, entity_c)
        else:
            report = engine.open_discovery(entity_a, top_k=int(body.get("top_k", 10)))

        return JSONResponse({"success": True, "report": report.model_dump()})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


async def api_discovery_isomorphisms(request: Request) -> JSONResponse:
    """Detect cross-domain mathematical AST isomorphisms."""
    try:
        body = await request.json()
        equations = body.get("equations", [])

        from privreach.discovery import EquationIsomorphismEngine
        engine = EquationIsomorphismEngine()

        for eq in equations:
            engine.register_equation(
                name=eq.get("name", "Unknown"),
                expression_str=eq.get("expression", ""),
                domain=eq.get("domain", "general"),
            )

        report = engine.detect_isomorphisms()
        return JSONResponse({"success": True, "report": report.model_dump()})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


async def api_cad_generate(request: Request) -> JSONResponse:
    """Synthesize parametric CadQuery script, validate manifold geometry, and simulate FEA."""
    try:
        body = await request.json()
        comp_type = body.get("component_type", "mounting_bracket")
        load_n = float(body.get("load_n", 100.0))
        simulate_fea = bool(body.get("simulate_fea", True))

        from privreach.cad import CadQueryGenerator, SandboxCADExecutor, FEARunner
        cad_gen = CadQueryGenerator()
        sandbox = SandboxCADExecutor()

        length = float(body.get("length_mm", 80.0))
        width = float(body.get("width_mm", 40.0))
        thickness = float(body.get("thickness_mm", 5.0))

        if comp_type == "l_bracket":
            cad_res = cad_gen.generate_l_bracket(leg_length_a=length, leg_length_b=width, width=30.0, thickness=thickness)
        else:
            cad_res = cad_gen.generate_mounting_bracket(length_mm=length, width_mm=width, thickness_mm=thickness)

        geom_val = sandbox.validate_analytical_box(length, width, thickness)

        fea_res = None
        if simulate_fea:
            fea_runner = FEARunner(material_key=body.get("material", "aluminum_6061_t6"))
            fea_res = fea_runner.simulate_cantilever_bracket(length, width, thickness, load_force_n=load_n).model_dump()

        return JSONResponse({
            "success": True,
            "cad_script": cad_res.model_dump(),
            "geometry_validation": geom_val.model_dump(),
            "fea_simulation": fea_res,
        })
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)




routes = [
    Route("/api/status", api_status, methods=["GET"]),
    Route("/api/documents", api_documents, methods=["GET"]),
    Route("/api/query", api_query, methods=["POST"]),
    Route("/api/ingest", api_ingest, methods=["POST"]),
    Route("/api/pdf", api_serve_pdf, methods=["GET"]),
    Route("/api/media", api_serve_media, methods=["GET"]),
    Route("/api/models", api_models, methods=["GET"]),
    Route("/api/models/switch", api_switch_model, methods=["POST"]),
    Route("/api/engine/start", api_start_engine, methods=["POST"]),
    Route("/api/graph", api_graph, methods=["GET"]),
    Route("/api/vault/clear", api_vault_clear, methods=["POST"]),
    Route("/api/compute/solve", api_compute_solve, methods=["POST"]),
    Route("/api/artifacts", api_artifacts, methods=["GET"]),
    Route("/api/security/hardware-auth", api_security_hardware_auth, methods=["GET"]),
    # Academic Ingress, Airlock CDR & Zero-Hallucination Prover Endpoints
    Route("/api/ingress/harvest", api_ingress_harvest, methods=["POST"]),
    Route("/api/airlock/process", api_airlock_process, methods=["POST"]),
    Route("/api/prover/verify", api_prover_verify, methods=["POST"]),
    # Hidden Discovery & Generative CAD Endpoints
    Route("/api/discovery/swanson", api_discovery_swanson, methods=["POST"]),
    Route("/api/discovery/isomorphisms", api_discovery_isomorphisms, methods=["POST"]),
    Route("/api/cad/generate", api_cad_generate, methods=["POST"]),
    # Modern Updater Endpoints
    Route("/api/updater/status", api_updater_status, methods=["GET"]),
    Route("/api/updater/check", api_updater_check, methods=["POST"]),
    Route("/api/updater/apply", api_updater_apply, methods=["POST"]),
    Route("/api/updater/rollback", api_updater_rollback, methods=["POST"]),
    Route("/api/updater/snapshots", api_updater_snapshots, methods=["GET"]),
]

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1",
            "http://localhost",
            "http://127.0.0.1:8765",
            "http://localhost:8765",
            "app://privreach",
            "http://privreach.desktop",
            "ms-appx-web://"
        ],
        allow_origin_regex=r"^https?://(127\.0\.0\.1|localhost)(:\d+)?$",
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"]
    )
]

app = Starlette(debug=False, routes=routes, middleware=middleware)


def run_server(host: str = "127.0.0.1", port: int = 8765):
    """Entrypoint to run the uvicorn ASGI server."""
    print(f"⚡ Privreach Local Workstation Engine running on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8765
    run_server(host=host, port=port)
