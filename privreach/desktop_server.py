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

    return JSONResponse({
        "status": "online",
        "engine_running": ollama_ok,
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
        "timestamp": time.time()
    })


async def api_documents(request: Request) -> JSONResponse:
    """Return all currently ingested documents in the Vault."""
    kernel = get_kernel()
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

    total_in_ram = kernel.total_chunks or len(kernel.bm25.chunks)
    if total_in_ram == 0:
        return JSONResponse({
            "error": "No documents ingested in vault. Please ingest a PDF textbook first.",
            "empty_vault": True
        }, status_code=400)

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


async def api_serve_pdf(request: Request) -> Response:
    """Serve a local PDF file for native rendering in WebView2."""
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
    """Serve local extracted figure images or media files."""
    media_path = request.query_params.get("path", "")
    if not media_path or not os.path.exists(media_path):
        return JSONResponse({"error": "Media file not found"}, status_code=404)

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
        allow_origins=["*"],
        allow_methods=["*"],
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
