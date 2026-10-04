"""Modern Web Dashboard for Privearch using Gradio."""

import os
import gradio as gr
from privearch.config import PrivearchConfig
from privearch.os_engine import PrivearchKernel
from privearch.schemas import VerificationStatus, RiskLevel
from privearch.updater.version import VERSION, BUILD_CHANNEL, RELEASE_DATE, DEFAULT_OTA_MANIFEST_URL
from privearch.updater.ota_manager import OTAManager


def build_app(kernel: PrivearchKernel):
    def handle_pdf_upload(files):
        if not files:
            return "No file selected."
        msg = []
        for f in files:
            file_path = f.name if hasattr(f, 'name') else str(f)
            res = kernel.ingest_pdf(file_path)
            msg.append(f"✓ Ingested **{res.get('doc_name')}**: {res.get('chunks')} chunks ({res.get('time_s')}s)")
        
        status = kernel.get_system_status()
        summary = (
            f"### Ingestion Complete\n\n" + "\n".join(msg) +
            f"\n\n**Total Chunks in RAM:** {status['indexed_chunks']} across {status['indexed_documents']} documents."
        )
        return summary

    def handle_query(query_text):
        if not query_text.strip():
            return (
                "Please enter a valid scientific question.",
                "",
                [],
                "No query provided.",
                ""
            )

        if kernel.total_chunks == 0:
            return (
                "⚠️ **No documents ingested yet!** Please upload or drag and drop a PDF textbook above first.",
                "",
                [],
                "Ingestion required.",
                ""
            )

        report = kernel.execute_rlcd(query_text)
        qa = report.query_analysis
        audit = report.verification

        # Router metadata markdown
        risk_badge = f"**Risk Level:** `{qa.risk_level.value}` | **Task:** `{qa.task_type.value}` | **Domain:** `{qa.scientific_domain}`"
        entities_str = f"**Key Entities:** {', '.join(qa.key_entities) if qa.key_entities else 'None'}"
        keywords_str = f"**BM25 Keywords:** {', '.join(qa.lexical_keywords)}"
        router_card = f"### 🧠 0.5B Router Analysis\n{risk_badge}\n\n{entities_str}\n\n{keywords_str}\n\n*Rationale:* {qa.analysis_rationale}"

        # Verification Matrix table data
        claims_table_data = []
        for c in audit.claims:
            icon = "✓ VERIFIED" if c.status == VerificationStatus.VERIFIED else (
                "⚠️ UNSUPPORTED" if c.status == VerificationStatus.UNSUPPORTED else (
                    "❌ CONTRADICTION" if c.status == VerificationStatus.CONTRADICTED else "⚡ PARTIAL"
                )
            )
            src = f"{c.source_doc} (p.{c.source_page})" if c.source_doc else "-"
            claims_table_data.append([
                c.claim_id,
                c.text,
                icon,
                src,
                f"{int(c.confidence*100)}%",
                c.critique or c.evidence_quote[:80]
            ])

        # Retrieved Passages markdown
        passages_md = [f"### 🔍 Retrieved Sources (RRF Top {len(report.retrieved_chunks)})"]
        for sc in report.retrieved_chunks:
            passages_md.append(
                f"**[{sc.final_rank}] {sc.chunk.doc_name} (Page {sc.chunk.page_num})**  \n"
                f"*RRF Score: {sc.rrf_score:.4f} | BM25: #{sc.bm25_rank or '-'} | FAISS: #{sc.dense_rank or '-'}*  \n"
                f"> {sc.chunk.text}\n"
            )
        passages_text = "\n\n---\n\n".join(passages_md)

        # Audit verdict summary
        audit_badge = f"### 🛡️ Adversarial Audit Verdict: `{audit.overall_verdict}`\n"
        audit_badge += f"**Grounding Score:** **{audit.grounding_score}%** ({audit.verified_count}/{audit.total_claims} verified, {audit.unsupported_count} unsupported)\n"
        audit_badge += f"\n*{audit.audit_summary}*"

        # Telemetry
        telemetry = (
            f"**Total Execution Time:** {report.execution_stats['total_elapsed_ms']} ms  \n"
            f"• Router: {report.execution_stats['stage_timings']['router_ms']} ms  \n"
            f"• Hybrid Retriever: {report.execution_stats['stage_timings']['retrieval_ms']} ms  \n"
            f"• Synthesis Engine (4B): {report.execution_stats['stage_timings']['synthesis_ms']} ms  \n"
            f"• Adversarial Verifier (0.5B): {report.execution_stats['stage_timings']['verifier_ms']} ms"
        )

        return (
            report.annotated_synthesis,
            audit_badge,
            claims_table_data,
            router_card,
            passages_text,
            telemetry
        )

    def handle_ota_check(custom_url):
        url = custom_url.strip() if custom_url and custom_url.strip() else DEFAULT_OTA_MANIFEST_URL
        manager = OTAManager(current_version=VERSION, manifest_url=url)
        has_update, manifest, msg = manager.check_for_updates()
        if not manifest:
            return (
                f"### ❌ Update Check Failed\n\n`{msg}`\n\nPlease check network connectivity or your manifest URL.",
                "",
                gr.update(interactive=False)
            )

        status_md = f"### {'🎉 New Update Available!' if has_update else '✅ Privearch is Up to Date'}\n\n"
        status_md += f"- **Current Installed Version:** `v{VERSION}` ({BUILD_CHANNEL})\n"
        status_md += f"- **Latest Version on Channel:** `v{manifest.get('version', 'Unknown')}`\n"
        status_md += f"- **Release Date:** `{manifest.get('release_date', 'Unknown')}`\n"
        status_md += f"- **SHA-256 Checksum:** `{manifest.get('sha256', 'Verified')}`\n"
        status_md += f"- **Status:** {msg}\n"

        changelog_md = f"### 📝 Release Notes for v{manifest.get('version')}\n\n{manifest.get('changelog', 'No release notes provided.')}"

        return (
            status_md,
            changelog_md,
            gr.update(interactive=True)
        )

    def handle_ota_install(custom_url):
        url = custom_url.strip() if custom_url and custom_url.strip() else DEFAULT_OTA_MANIFEST_URL
        app_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        manager = OTAManager(current_version=VERSION, manifest_url=url, install_dir=app_dir)
        has_update, manifest, msg = manager.check_for_updates()
        if not manifest:
            return f"❌ Cannot proceed with update: {msg}"

        ok, zip_or_err = manager.download_update(manifest)
        if not ok:
            return f"❌ Download / Checksum verification failed: {zip_or_err}"

        app_ok, app_msg = manager.apply_update(zip_or_err)
        if not app_ok:
            return f"❌ Failed to apply update: {app_msg}"

        return (
            f"### 🎉 Update Successfully Installed!\n\n"
            f"- **New Version:** `v{manifest.get('version')}`\n"
            f"- **Vault Integrity:** Existing chemistry PDF index (`.privearch_cache/`) was safely preserved.\n\n"
            f"**Please restart Privearch to activate the new version.**"
        )

    def handle_ota_rollback():
        app_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        manager = OTAManager(install_dir=app_dir)
        ok, msg = manager.rollback()
        if ok:
            return f"### ✅ Rollback Successful\n\n{msg}\nPlease restart Privearch."
        else:
            return f"### ❌ Rollback Failed\n\n{msg}"

    with gr.Blocks(title="Privearch OS - Zero-Trust Scientific Synthesis") as demo:
        gr.Markdown(
            f"""
            # ⚡ Privearch Operating System
            ### Zero-Trust, 100% Local Scientific Synthesis with Dual-Model Adversarial Verification
            *v{VERSION} ({BUILD_CHANNEL})  •  CPU embeddings + 4GB VRAM  •  Zero data leaves this machine.*
            """
        )

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 📚 Dynamic PDF Ingestion")
                pdf_upload = gr.File(
                    label="Drag & Drop scientific PDFs",
                    file_types=[".pdf"],
                    file_count="multiple"
                )
                upload_btn = gr.Button("Vectorize & Update In-RAM Index", variant="primary")
                ingest_output = gr.Markdown("Ready to ingest documents.")
                upload_btn.click(handle_pdf_upload, inputs=[pdf_upload], outputs=[ingest_output])

            with gr.Column(scale=2):
                gr.Markdown("### 🔬 Scientific Query Console")
                query_input = gr.Textbox(
                    label="Ask a scientific / chemical question",
                    placeholder="e.g. State and explain Henry's law with its mathematical form and applications.",
                    lines=2
                )
                with gr.Row():
                    submit_btn = gr.Button("Execute RLCD Pipeline", variant="primary")
                    clear_btn = gr.Button("Clear")

                gr.Examples(
                    examples=[
                        "What is Henry's law, its mathematical formula, and its application in scuba diving?",
                        "Explain Raoult's law for volatile solutes and how ideal solutions obey it.",
                        "What is Le Chatelier's principle and how does pressure change affect equilibrium?",
                    ],
                    inputs=[query_input]
                )

        gr.Markdown("---")
        
        with gr.Tabs():
            with gr.TabItem("📖 Peer-Reviewed Synthesis"):
                synthesis_md = gr.Markdown("Synthesis will appear here after execution.")
                telemetry_md = gr.Markdown("")

            with gr.TabItem("🛡️ Adversarial Claim Audit Matrix"):
                audit_summary_md = gr.Markdown("Audit summary will appear here.")
                claims_table = gr.Dataframe(
                    headers=["ID", "Atomic Claim", "Audit Status", "Source Reference", "Confidence", "Critique / Evidence"],
                    datatype=["number", "str", "str", "str", "str", "str"],
                    interactive=False
                )

            with gr.TabItem("🧠 0.5B Router Telemetry"):
                router_md = gr.Markdown("Router analysis will appear here.")

            with gr.TabItem("🔍 Hybrid Retrieved Passages"):
                passages_box = gr.Markdown("Retrieved text chunks will appear here.")

            with gr.TabItem("🔄 OTA System Updates"):
                gr.Markdown(
                    f"""
                    ### 🔄 Over-The-Air (OTA) System Updates
                    Privearch includes a zero-trust, cryptographically verified OTA update manager.
                    - **Installed Version:** `v{VERSION}` ({BUILD_CHANNEL})
                    - **Release Date:** `{RELEASE_DATE}`
                    - **Vault Protection:** Existing `.privearch_cache/` indexes are strictly preserved across updates.
                    """
                )
                with gr.Row():
                    ota_url_input = gr.Textbox(
                        label="OTA Manifest URL or Local Path",
                        value=DEFAULT_OTA_MANIFEST_URL,
                        lines=1
                    )
                with gr.Row():
                    ota_check_btn = gr.Button("🔍 Check for Updates", variant="primary")
                    ota_install_btn = gr.Button("⚡ Download & Apply Update", variant="stop", interactive=False)
                    ota_rollback_btn = gr.Button("↩️ Rollback to Previous Version", variant="secondary")

                ota_status_md = gr.Markdown("Click 'Check for Updates' to verify the latest release.")
                ota_changelog_md = gr.Markdown("")
                ota_result_md = gr.Markdown("")

                ota_check_btn.click(
                    handle_ota_check,
                    inputs=[ota_url_input],
                    outputs=[ota_status_md, ota_changelog_md, ota_install_btn]
                )
                ota_install_btn.click(
                    handle_ota_install,
                    inputs=[ota_url_input],
                    outputs=[ota_result_md]
                )
                ota_rollback_btn.click(
                    handle_ota_rollback,
                    inputs=[],
                    outputs=[ota_result_md]
                )

        submit_btn.click(
            handle_query,
            inputs=[query_input],
            outputs=[synthesis_md, audit_summary_md, claims_table, router_md, passages_box, telemetry_md]
        )
        clear_btn.click(lambda: ("", "", "", [], "", ""), outputs=[query_input, synthesis_md, audit_summary_md, claims_table, router_md, passages_box])

    return demo


import socket

def find_available_port(start_port: int = 7860, max_tries: int = 50) -> int:
    """Find an unbound port starting from start_port."""
    for p in range(start_port, start_port + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    return start_port


def launch_web(port: int = 7860, share: bool = False):
    import sys
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    config = PrivearchConfig()
    kernel = PrivearchKernel(config)
    st = kernel.get_system_status()
    print(f"[OK] Privearch Web UI initialized with {st['indexed_chunks']} chunks across {st['indexed_documents']} chemistry PDFs.")

    # Find next available port to prevent OSError if 7860 is busy
    initial_port = int(os.getenv("GRADIO_SERVER_PORT", str(port)))
    target_port = find_available_port(initial_port)
    print(f"[INFO] Launching Privearch Web Dashboard on: http://127.0.0.1:{target_port}")

    demo = build_app(kernel)
    try:
        demo.launch(server_name="127.0.0.1", server_port=target_port, share=share)
    except OSError:
        fallback_port = find_available_port(target_port + 1)
        print(f"[WARN] Port {target_port} was occupied, redirecting to: http://127.0.0.1:{fallback_port}")
        demo.launch(server_name="127.0.0.1", server_port=fallback_port, share=share)


if __name__ == "__main__":
    launch_web()
