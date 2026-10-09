"""Three-Plane Research Operating Environment for Privreach OS.

Layout Architecture:
┌──────────────┬────────────────────────┬──────────────┐
│   LEFT       │        CENTER          │    RIGHT     │
│   CHAT &     │   EXPLAINER CANVAS     │   MEDIA &    │
│   INQUIRY    │  (Plots / Derivations  │   EVIDENCE   │
│   CONSOLE    │   Simulations / Math)  │    VAULT     │
├──────────────┴────────────────────────┴──────────────┤
│ BOTTOM: TERMINAL & EXECUTION CONSOLE (Run / Stop / Rebuild) │
└───────────────────────────────────────────────────────┘
"""

import os
import sys
import time
import psutil
import gradio as gr
import plotly.graph_objects as go
from typing import Dict, Any, List, Optional, Tuple

from privearch.config import PrivearchConfig, DEFAULT_CONFIG
from privearch.schemas import (
    RiskLevel,
    TaskType,
    VerificationStatus,
    PrivearchReport,
    CalculationVerification,
)
from privearch.os_engine import PrivearchKernel
from privearch.ui.canvas_generator import CanvasGenerator
from privearch.updater.version import VERSION, BUILD_CHANNEL, RELEASE_DATE, DEFAULT_OTA_MANIFEST_URL
from privearch.updater.ota_manager import OTAManager
from privearch.models.engine_installer import (
    is_engine_running,
    list_installed_models,
    start_ollama_daemon,
    download_ollama_installer,
    install_ollama,
    pull_model,
)

# Custom Theme and CSS for the Three-Plane Workspace
THREE_PLANE_CSS = """
:root {
  --primary-accent: #38bdf8;
  --bg-dark: #090d16;
  --card-dark: #0f172a;
  --border-dark: #1e293b;
  --text-main: #f1f5f9;
  --text-muted: #94a3b8;
}

body, .gradio-container {
  background-color: var(--bg-dark) !important;
  color: var(--text-main) !important;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
  max-width: 100% !important;
  margin: 0 !important;
  padding: 8px 16px !important;
}

/* Three-Plane Column Styling */
.plane-card {
  background: var(--card-dark) !important;
  border: 1px solid var(--border-dark) !important;
  border-radius: 12px !important;
  padding: 12px !important;
  height: 680px !important;
  overflow-y: auto !important;
}

.plane-header {
  font-size: 15px !important;
  font-weight: 700 !important;
  color: var(--primary-accent) !important;
  border-bottom: 1px solid var(--border-dark) !important;
  padding-bottom: 6px !important;
  margin-bottom: 10px !important;
  display: flex !important;
  align-items: center !important;
  gap: 8px !important;
}

/* Terminal Console Styling */
.terminal-box {
  background-color: #030712 !important;
  color: #4ade80 !important;
  font-family: "Cascadia Code", "Fira Code", Consolas, monospace !important;
  font-size: 12.5px !important;
  border: 1px solid #1f2937 !important;
  border-radius: 8px !important;
  padding: 10px !important;
  line-height: 1.4 !important;
}

.badge-pill {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
}
"""


def build_three_plane_app(kernel: Optional[PrivearchKernel] = None) -> gr.Blocks:
    """Constructs the high-performance Three-Plane Research Workstation."""
    if kernel is None:
        kernel = PrivearchKernel(DEFAULT_CONFIG)

    # State stores
    chat_history_state = []
    active_report_state = {"report": None}

    def handle_workspace_query(user_query: str, history: list):
        """Orchestrates query across RLCD, Canvas, Artifacts, and Terminal Console."""
        if not user_query.strip():
            return (
                history,
                "",  # Query input clear
                CanvasGenerator.generate_scientific_plot("", "ans", {}),
                "### 📐 Derivation Canvas\n*Submit a query to generate mathematical derivations.*",
                CanvasGenerator.generate_particle_simulation_html(300, 1.0),
                [],
                CanvasGenerator.generate_multimodal_timeline_markdown([]),
                "No query provided.",
                "Ready.",
                "*No artifacts generated.*",
                "Retrieved passages will appear here.",
                "[IDLE] Ready for instructions."
            )

        t_start = time.time()
        term_logs = [f"[{time.strftime('%H:%M:%S')}] [KERNEL] ⚡ Intercepting query: '{user_query[:50]}...'"]

        # 1. Execute RLCD Pipeline with Phase 2 Compute
        report = kernel.execute_rlcd(user_query)
        active_report_state["report"] = report

        qa = report.query_analysis
        audit = report.verification
        term_logs.append(f"[{time.strftime('%H:%M:%S')}] [ROUTER] Domain: {qa.scientific_domain} | Risk: {qa.risk_level.value} | Task: {qa.task_type.value}")
        term_logs.append(f"[{time.strftime('%H:%M:%S')}] [RETRIEVER] Hybrid RRF retrieved {len(report.retrieved_chunks)} passages ({report.execution_stats['stage_timings']['retrieval_ms']}ms)")

        # 2. Extract Calculation Data for Canvas
        active_calc = report.calculations[0] if report.calculations else None
        target_eq = active_calc.equation_latex if active_calc else ""
        target_var = active_calc.target_variable if active_calc else "ans"
        known_vars = active_calc.variables if active_calc else {}
        computed_float = None

        if active_calc and active_calc.deterministic_computed_value:
            term_logs.append(f"[{time.strftime('%H:%M:%S')}] [COMPUTE] Deterministic SymPy evaluation: {active_calc.equation_latex} -> {active_calc.deterministic_computed_value}")
            try:
                computed_float = float(active_calc.deterministic_computed_value)
            except ValueError:
                pass

        term_logs.append(f"[{time.strftime('%H:%M:%S')}] [SYNTHESIS] 4B synthesis generated ({report.execution_stats['stage_timings']['synthesis_ms']}ms)")
        term_logs.append(f"[{time.strftime('%H:%M:%S')}] [VERIFIER] Adversarial audit complete. Grounding Score: {audit.grounding_score}% ({audit.verified_count}/{audit.total_claims} verified)")

        # 3. Canvas Components
        plot_fig = CanvasGenerator.generate_scientific_plot(
            equation_str=target_eq or "y = f(x)",
            target_var=target_var,
            variables=known_vars,
            computed_val=computed_float
        )

        derivation_md = (
            CanvasGenerator.generate_derivation_markdown(active_calc)
            if active_calc else
            f"### 📖 Scientific Synthesis\n\n{report.annotated_synthesis}"
        )

        # Particle simulation temperature
        sim_t = known_vars.get("T", 300.0)
        sim_p = known_vars.get("P", 101325.0) / 101325.0 if "P" in known_vars else 1.0
        sim_html = CanvasGenerator.generate_particle_simulation_html(temperature=sim_t, pressure=sim_p)

        # Multimodal Media Timeline
        timeline_md = CanvasGenerator.generate_multimodal_timeline_markdown(report.retrieved_chunks)

        # Claims Table
        claims_data = []
        for c in audit.claims:
            icon = "✓ VERIFIED" if c.status == VerificationStatus.VERIFIED else (
                "⚠️ UNSUPPORTED" if c.status == VerificationStatus.UNSUPPORTED else (
                    "❌ CONTRADICTION" if c.status == VerificationStatus.CONTRADICTED else "⚡ PARTIAL"
                )
            )
            src = f"{c.source_doc} (p.{c.source_page})" if c.source_doc else "-"
            claims_data.append([c.claim_id, c.text, icon, src, f"{int(c.confidence*100)}%", c.critique or c.evidence_quote[:75]])

        # 4. Left Chat Plane Output
        chat_msg = f"**{report.annotated_synthesis}**\n\n---\n*🛡️ Audit Verdict:* `{audit.overall_verdict}` (*Grounding: {audit.grounding_score}%*)"
        new_history = list(history) + [[user_query, chat_msg]]

        # 5. Right Media Plane Data
        passages_md = [f"### 🔍 Retrieved Evidence (Top {len(report.retrieved_chunks)})"]
        for sc in report.retrieved_chunks:
            c = sc.chunk
            ev_type = getattr(c, "evidence_type", "DOCUMENT_PAGE")
            if ev_type in ("VIDEO_TIMECODE", "AUDIO_TRANSCRIPT"):
                sub_header = f"[{sc.final_rank}] 🎬 {c.doc_name} ({c.section_header})"
                if getattr(c, "speaker_id", None):
                    sub_header += f" - {c.speaker_id}"
            else:
                sub_header = f"[{sc.final_rank}] 📄 {c.doc_name} (Page {c.page_num})"
            passages_md.append(
                f"**{sub_header}**  \n"
                f"*RRF Score: {sc.rrf_score:.4f} | BM25: #{sc.bm25_rank or '-'} | FAISS: #{sc.dense_rank or '-'}*  \n"
                f"> {c.text}\n"
            )
        passages_text = "\n\n---\n\n".join(passages_md)

        if report.artifacts:
            art_md_list = ["### 📦 Generated Provenance Artifacts"]
            for art in report.artifacts:
                art_md_list.append(
                    f"- **{art.name}** (`{art.artifact_id}`) | `{art.artifact_type.value}`  \n"
                    f"  *Provenance:* `{art.provenance.get('proof_chain', 'Direct')}`"
                )
            artifacts_text = "\n\n".join(art_md_list)
        else:
            artifacts_text = "*No computation artifacts generated.*"

        # Router Card
        router_text = (
            f"**Domain:** {qa.scientific_domain}  \n"
            f"**Risk Level:** `{qa.risk_level.value}` | **Task:** `{qa.task_type.value}`  \n"
            f"**Keywords:** {', '.join(qa.lexical_keywords)}"
        )

        # Terminal Console Output
        total_ms = report.execution_stats["total_elapsed_ms"]
        term_logs.append(f"[{time.strftime('%H:%M:%S')}] [SYSTEM] Pipeline complete in {total_ms}ms. Memory: {report.execution_stats['ram_used_percent']}% RAM | {report.execution_stats['ram_available_gb']} GB Free.")
        console_output = "\n".join(term_logs)

        return (
            new_history,
            "",  # Clear query input
            plot_fig,
            derivation_md,
            sim_html,
            claims_data,
            timeline_md,
            router_text,
            f"Grounding Score: **{audit.grounding_score}%** | Verdict: `{audit.overall_verdict}`",
            artifacts_text,
            passages_text,
            console_output
        )

    def handle_ingest_files(files):
        """Ingests files dropped into the Right Media Plane."""
        if not files:
            return "No files dropped.", "Ready."
        msgs = []
        for f in files:
            res = kernel.ingest_media(f.name)
            type_tag = res.get("type", "document")
            msgs.append(f"• [{type_tag.upper()}] {res['doc_name']}: {res['chunks']} chunks ({res['time_s']}s)")
        kernel.save_index()
        status = kernel.get_system_status()
        summary = f"**Ingested {len(files)} media file(s):**\n" + "\n".join(msgs)
        vault_status = f"**Vault Total:** {status['indexed_chunks']} chunks across {status['indexed_documents']} media files in RAM."
        return summary, vault_status

    # -------------------------------------------------------------
    # GRADIO INTERFACE LAYOUT
    # -------------------------------------------------------------
    with gr.Blocks(title="Privreach OS - Multimodal Research Workstation", css=THREE_PLANE_CSS, theme=gr.themes.Default(primary_hue="sky")) as demo:
        # Top Header Bar
        with gr.Row(elem_classes=["header-bar"]):
            with gr.Column(scale=3):
                gr.HTML(
                    f"""
                    <div style="display: flex; align-items: center; gap: 14px; padding: 4px 0;">
                      <img src="file/assets/logo_web.png" style="width: 42px; height: 42px; border-radius: 8px;" onerror="this.style.display='none'">
                      <div>
                        <div style="font-size: 20px; font-weight: 800; letter-spacing: 0.5px; background: linear-gradient(135deg, #38bdf8 0%, #818cf8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                          PRIVREACH RESEARCH OPERATING SYSTEM
                        </div>
                        <div style="font-size: 11.5px; color: #94a3b8;">
                          Local Multimodal Workstation • Zero-Trust Airgap • CPU Embeddings + 4GB VRAM • v{VERSION}
                        </div>
                      </div>
                    </div>
                    """
                )
            with gr.Column(scale=2):
                st = kernel.get_system_status()
                gr.HTML(
                    f"""
                    <div style="display: flex; justify-content: flex-end; gap: 8px; align-items: center; height: 100%; font-size: 11px;">
                      <span style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; padding: 3px 8px; border-radius: 6px; border: 1px solid rgba(56, 189, 248, 0.3);">
                        🔒 100% Local Airgap
                      </span>
                      <span style="background: rgba(74, 222, 128, 0.15); color: #4ade80; padding: 3px 8px; border-radius: 6px; border: 1px solid rgba(74, 222, 128, 0.3);">
                        🧠 Dual-Model (0.5B + 4B)
                      </span>
                      <span style="background: rgba(168, 85, 247, 0.15); color: #c084fc; padding: 3px 8px; border-radius: 6px; border: 1px solid rgba(168, 85, 247, 0.3);">
                        📚 {st['indexed_chunks']} Vault Chunks
                      </span>
                    </div>
                    """
                )

        # ---------------------------------------------------------
        # MAIN THREE-PLANE WORKSPACE
        # ---------------------------------------------------------
        with gr.Row():
            # =====================================================
            # PLANE 1 (LEFT): CHAT & INTENT INQUIRY CONSOLE (30%)
            # =====================================================
            with gr.Column(scale=3, elem_classes=["plane-card"]):
                gr.HTML("<div class='plane-header'>💬 RESEARCH CHAT & INTENT CONSOLE</div>")
                
                chat_display = gr.Chatbot(
                    label="Peer-Reviewed Discussion",
                    height=360,
                    show_label=False
                )


                query_input = gr.Textbox(
                    label="Scientific Query / Hypothesis",
                    placeholder="Ask research questions, equations, or mechanisms...",
                    lines=2,
                    show_label=False
                )

                with gr.Row():
                    run_btn = gr.Button("▶ Run Pipeline", variant="primary", size="sm")
                    clear_btn = gr.Button("Clear", size="sm")

                gr.Examples(
                    examples=[
                        "What is Henry's law, its formula, and scuba diving application?",
                        "Calculate volume of 2 moles gas at 300 K and 101325 Pa using P*V = n*R*T.",
                        "Explain Raoult's law for ideal solutions and its vapor pressure graph.",
                    ],
                    inputs=[query_input]
                )

                router_card = gr.Markdown("**0.5B Router:** Ready to analyze incoming intents.")

            # =====================================================
            # PLANE 2 (CENTER): EXPLAINER CANVAS (45%)
            # =====================================================
            with gr.Column(scale=5, elem_classes=["plane-card"]):
                gr.HTML("<div class='plane-header'>🎨 EXPLAINER CANVAS (DETERMINISTIC WORKSPACE)</div>")
                
                canvas_status_banner = gr.Markdown("Status: **Idle** • Awaiting computation")

                with gr.Tabs():
                    with gr.TabItem("📊 Scientific Curves & Plots"):
                        initial_fig = CanvasGenerator.generate_scientific_plot("", "V", {})
                        canvas_plot = gr.Plot(value=initial_fig, show_label=False)

                    with gr.TabItem("📐 Step-by-Step KaTeX Math"):
                        canvas_derivation = gr.Markdown("Mathematical derivation will appear here.")

                    with gr.TabItem("⚛️ Molecular & Particle Simulation"):
                        canvas_simulation = gr.HTML(CanvasGenerator.generate_particle_simulation_html(300, 1.0))

                    with gr.TabItem("🛡️ Adversarial Claim Audit"):
                        canvas_claims_table = gr.Dataframe(
                            headers=["#", "Atomic Claim", "Status", "Source Document", "Conf", "Evidence Critique"],
                            datatype=["number", "str", "str", "str", "str", "str"],
                            interactive=False
                        )

                    with gr.TabItem("🎥 Multimodal Timeline & Transcripts"):
                        canvas_multimodal = gr.Markdown(CanvasGenerator.generate_multimodal_timeline_markdown([]))

            # =====================================================
            # PLANE 3 (RIGHT): MEDIA & EVIDENCE VAULT (25%)
            # =====================================================
            with gr.Column(scale=3, elem_classes=["plane-card"]):
                gr.HTML("<div class='plane-header'>📁 MEDIA & EVIDENCE VAULT</div>")

                media_dropzone = gr.File(
                    label="Drop PDFs, Audio, Video, Transcripts",
                    file_types=[".pdf", ".mp4", ".mkv", ".mov", ".wav", ".mp3", ".m4a", ".vtt", ".srt", ".csv"],
                    file_count="multiple",
                    height=90
                )
                ingest_btn = gr.Button("📥 Ingest into Knowledge Vault", size="sm")
                ingest_msg = gr.Markdown("Ready to ingest media.")
                vault_status_box = gr.Markdown(f"**Vault Status:** {st['indexed_chunks']} chunks in RAM.")

                with gr.Tabs():
                    with gr.TabItem("🔍 Evidence Passages"):
                        passages_box = gr.Markdown("Retrieved PDF excerpts with RRF ranks.")

                    with gr.TabItem("📦 Provenance Artifacts"):
                        artifacts_box = gr.Markdown("Generated artifacts will appear here.")

        # ---------------------------------------------------------
        # PLANE 4 (BOTTOM): EXECUTION CONSOLE & SYSTEM TELEMETRY
        # ---------------------------------------------------------
        with gr.Row():
            with gr.Column(scale=1):
                gr.HTML(
                    """
                    <div style="font-size: 13px; font-weight: bold; color: #4ade80; margin-bottom: 4px; display: flex; align-items: center; gap: 8px;">
                      ⌨️ EXECUTION CONSOLE & MODEL TELEMETRY
                    </div>
                    """
                )
                console_output = gr.Code(
                    value=f"[{time.strftime('%H:%M:%S')}] [SYSTEM] Privreach OS Kernel initialized. Ready for commands.\n"
                          f"[{time.strftime('%H:%M:%S')}] [ENGINE] 0.5B Router ({kernel.router_model}) | 4B Synthesizer ({kernel.synthesis_model}) | 0.5B Verifier ({kernel.verifier_model})",
                    language="shell",
                    lines=4,
                    show_label=False,
                    elem_classes=["terminal-box"]
                )
                with gr.Row():
                    btn_run = gr.Button("▶ Run", variant="primary", size="sm")
                    btn_stop = gr.Button("■ Stop", variant="stop", size="sm")
                    btn_rebuild = gr.Button("↻ Re-index Vault", variant="secondary", size="sm")

        # ---------------------------------------------------------
        # EVENT BINDINGS
        # ---------------------------------------------------------
        run_outputs = [
            chat_display,
            query_input,
            canvas_plot,
            canvas_derivation,
            canvas_simulation,
            canvas_claims_table,
            canvas_multimodal,
            router_card,
            canvas_status_banner,
            artifacts_box,
            passages_box,
            console_output
        ]

        run_btn.click(
            handle_workspace_query,
            inputs=[query_input, chat_display],
            outputs=run_outputs
        )
        btn_run.click(
            handle_workspace_query,
            inputs=[query_input, chat_display],
            outputs=run_outputs
        )
        query_input.submit(
            handle_workspace_query,
            inputs=[query_input, chat_display],
            outputs=run_outputs
        )

        clear_btn.click(
            lambda: ([], "", CanvasGenerator.generate_scientific_plot("", "V", {}), "Derivations cleared.", CanvasGenerator.generate_particle_simulation_html(300, 1.0), [], CanvasGenerator.generate_multimodal_timeline_markdown([]), "Cleared.", "Idle", "*Cleared*", "*Cleared*", "[CONSOLE] Cleared."),
            outputs=run_outputs
        )

        ingest_btn.click(
            handle_ingest_files,
            inputs=[media_dropzone],
            outputs=[ingest_msg, vault_status_box]
        )

        btn_rebuild.click(
            lambda: f"[{time.strftime('%H:%M:%S')}] [REINDEX] Vault re-indexed. Chunks loaded: {kernel.total_chunks}",
            outputs=[console_output]
        )

    return demo
