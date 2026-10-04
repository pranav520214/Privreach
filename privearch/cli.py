"""Privearch Interactive Terminal Operating System Interface."""

import os
import sys
import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Prompt
from rich.text import Text

from privearch.config import PrivearchConfig
from privearch.os_engine import PrivearchKernel
from privearch.schemas import VerificationStatus, RiskLevel


# Ensure UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console()

BANNER = """[bold cyan]
 ██████╗ ██████╗ ██╗██╗   ██╗███████╗ █████╗ ██████╗  ██████╗██╗  ██╗
 ██╔══██╗██╔══██╗██║██║   ██║██╔════╝██╔══██╗██╔══██╗██╔════╝██║  ██║
 ██████╔╝██████╔╝██║██║   ██║█████╗  ███████║██████╔╝██║     ███████║
 ██╔═══╝ ██╔══██╗██║╚██╗ ██╔╝██╔══╝  ██╔══██║██╔══██╗██║     ██╔══██║
 ██║     ██║  ██║██║ ╚████╔╝ ███████╗██║  ██║██║  ██║╚██████╗██║  ██║
 ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝  ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝[/bold cyan]
[bold white]  ⚡ ZERO-TRUST LOCAL SCIENTIFIC OPERATING SYSTEM  |  CPU + 4GB VRAM[/bold white]
[dim green]  🔒 100% Local Airgap  •  🧠 Dual-Model Brain-Trust  •  🛡️ Adversarial Claim Audit[/dim green]
"""


def display_welcome(kernel: PrivearchKernel):
    console.print(BANNER)
    status = kernel.get_system_status()

    table = Table(title="[bold yellow]PRIVEARCH OS KERNEL TELEMETRY[/bold yellow]", border_style="cyan")
    table.add_column("Subsystem", style="bold white", width=22)
    table.add_column("Configuration / Telemetry", style="green")

    table.add_row("Privearch OS Version", "[bold cyan]v1.0.0[/bold cyan] (Stable Channel • OTA Enabled)")
    table.add_row("Dual-Model Router", f"[magenta]{status['router_model']}[/magenta] (0.5B Administrative)")
    table.add_row("Synthesis Engine", f"[magenta]{status['synthesis_model']}[/magenta] (Deep Academic Synthesis)")
    table.add_row("Adversarial Verifier", f"[magenta]{status['verifier_model']}[/magenta] (0.5B Claim Auditor)")
    table.add_row("In-RAM Hybrid Index", f"{status['indexed_documents']} Docs  |  {status['indexed_chunks']} Chunks (Okapi BM25 + FAISS RRF)")
    table.add_row("Vector Embeddings", f"{status['embedding_engine']} (100% Local CPU Vectorization)")
    table.add_row("Host Hardware RAM", f"{status['host_ram_used_percent']}% Used ({status['host_ram_free_gb']} GB Free)")
    table.add_row("Security Posture", "[bold green]100% AIRGAPPED & LOCAL (Zero Egress)[/bold green]")

    console.print(table)
    console.print()
    console.print("[dim yellow]💡 Instructions: Drag & drop any PDF path into the prompt, or enter a scientific question.[/dim yellow]")
    console.print("[dim yellow]   Commands: /scan (ingest PDFs)  |  /status  |  /engine (manage models)  |  /update  |  /exit[/dim yellow]\n")



def display_rlcd_report(report):
    console.print("\n" + "=" * 80)
    
    # 1. Router Analysis Card
    qa = report.query_analysis
    risk_colors = {
        RiskLevel.CRITICAL: "bold red on white",
        RiskLevel.HIGH: "bold red",
        RiskLevel.MEDIUM: "bold yellow",
        RiskLevel.LOW: "bold green"
    }
    r_color = risk_colors.get(qa.risk_level, "white")
    
    router_panel = Panel(
        f"[bold]Domain:[/bold] {qa.scientific_domain}\n"
        f"[bold]Risk Level:[/bold] [{r_color}] {qa.risk_level.value} [/{r_color}]\n"
        f"[bold]Task Type:[/bold] {qa.task_type.value}\n"
        f"[bold]Key Entities:[/bold] {', '.join(qa.key_entities) if qa.key_entities else 'None'}\n"
        f"[bold]BM25 Keywords:[/bold] {', '.join(qa.lexical_keywords)}\n"
        f"[bold]Rationale:[/bold] {qa.analysis_rationale}",
        title="[bold magenta]🧠 STAGE 1: 0.5B QUERY ANALYZER (ROUTER)[/bold magenta]",
        border_style="magenta"
    )
    console.print(router_panel)

    # 2. Hybrid Retrieval Table
    ret_table = Table(title="[bold cyan]🔍 STAGE 2: HYBRID RETRIEVER (OKAPI BM25 + FAISS RRF)[/bold cyan]", border_style="cyan")
    ret_table.add_column("Cite", style="bold yellow", width=6)
    ret_table.add_column("Source Document", style="white", width=22)
    ret_table.add_column("Page", style="cyan", width=6)
    ret_table.add_column("BM25 Rank", style="dim", width=10)
    ret_table.add_column("Dense Rank", style="dim", width=11)
    ret_table.add_column("RRF Score", style="bold green", width=10)
    ret_table.add_column("Excerpt", style="dim white")

    for sc in report.retrieved_chunks:
        excerpt = sc.chunk.text[:95].replace('\n', ' ') + "..."
        b_rank = f"#{sc.bm25_rank}" if sc.bm25_rank else "-"
        d_rank = f"#{sc.dense_rank}" if sc.dense_rank else "-"
        ret_table.add_row(
            f"[{sc.final_rank}]",
            sc.chunk.doc_name,
            str(sc.chunk.page_num),
            b_rank,
            d_rank,
            f"{sc.rrf_score:.4f}",
            excerpt
        )
    console.print(ret_table)

    # 3. Adversarial Claim Verification Matrix
    audit = report.verification
    v_color = "bold green" if audit.grounding_score >= 80 else ("bold yellow" if audit.grounding_score >= 50 else "bold red")

    claim_table = Table(
        title=f"[bold red]🛡️ STAGE 4: 0.5B ADVERSARIAL CLAIM AUDIT (Grounding Score: [{v_color}]{audit.grounding_score}%[/{v_color}])[/bold red]",
        border_style="red"
    )
    claim_table.add_column("#", style="bold white", width=4)
    claim_table.add_column("Atomic Claim Tested", style="white", width=34)
    claim_table.add_column("Status", width=14)
    claim_table.add_column("Source & Page", style="cyan", width=18)
    claim_table.add_column("Audit Critique / Evidence", style="dim white")

    status_badges = {
        VerificationStatus.VERIFIED: "[bold green]VERIFIED ✓[/bold green]",
        VerificationStatus.UNSUPPORTED: "[bold red]UNSUPPORTED ⚠️[/bold red]",
        VerificationStatus.CONTRADICTED: "[bold white on red]CONTRADICTION ❌[/bold white on red]",
        VerificationStatus.PARTIAL: "[bold yellow]PARTIAL ⚡[/bold yellow]"
    }

    for c in audit.claims:
        badge = status_badges.get(c.status, str(c.status))
        src = f"{c.source_doc} (p.{c.source_page})" if c.source_doc else "-"
        critique = c.critique or c.evidence_quote[:70]
        claim_table.add_row(
            str(c.claim_id),
            c.text[:100] + ("..." if len(c.text) > 100 else ""),
            badge,
            src,
            critique
        )
    console.print(claim_table)

    # 4. Final Scientific Synthesis Card
    console.print()
    synthesis_panel = Panel(
        Markdown(report.annotated_synthesis),
        title="[bold green]🔬 STAGE 3: SYNTHESIS ENGINE (GROUNDED PEER-REVIEW ANSWER)[/bold green]",
        border_style="green",
        subtitle=f"[dim]Audit Verdict: {audit.overall_verdict}  |  Latency: {report.execution_stats['total_elapsed_ms']}ms[/dim]"
    )
    console.print(synthesis_panel)
    console.print("=" * 80 + "\n")


def run_cli():
    """Main CLI loop."""
    config = PrivearchConfig()
    
    # Check if local inference engine is running / installed
    from privearch.models.engine_installer import is_engine_running, find_ollama_executable, bootstrap_system
    if not is_engine_running():
        console.print("[bold yellow]⚠️ Local AI Inference Engine (Ollama) is not running or not installed.[/bold yellow]")
        do_setup = Prompt.ask(
            "[bold cyan]Would you like Privearch to automatically download, install, and configure Ollama now?[/bold cyan]",
            choices=["y", "n"],
            default="y"
        )
        if do_setup == "y":
            from privearch.models.engine_installer import main as engine_setup_main
            engine_setup_main()

    console.print("[dim cyan]Booting Privearch OS Kernel...[/dim cyan]")
    try:
        kernel = PrivearchKernel(config)
    except Exception as e:
        console.print(f"[bold red]Failed to boot Privearch Kernel: {e}[/bold red]")
        sys.exit(1)

    display_welcome(kernel)


    # Check if there are local PDFs in the chemistry directory and suggest ingest
    current_dir = os.path.abspath(".")
    local_pdfs = [f for f in os.listdir(current_dir) if f.lower().endswith(".pdf")]
    if local_pdfs and kernel.total_chunks == 0:
        auto = Prompt.ask(
            f"[bold yellow]Found {len(local_pdfs)} chemistry textbook PDFs in this directory. Ingest them now into RAM index?[/bold yellow]",
            choices=["y", "n"],
            default="y"
        )
        if auto == "y":
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                console=console
            ) as progress:
                t = progress.add_task("[cyan]Ingesting local scientific PDFs...", total=len(local_pdfs))
                for pdf in local_pdfs[:5]:  # Ingest top 5 for instant boot, or all
                    progress.update(t, description=f"[cyan]Ingesting {pdf}...")
                    kernel.ingest_pdf(os.path.join(current_dir, pdf))
                    progress.advance(t)
            console.print(f"[bold green]✓ Ingested! RAM Index now contains {kernel.total_chunks} semantic chunks across {len(kernel.ingested_files)} PDFs.[/bold green]\n")

    while True:
        try:
            user_input = Prompt.ask("[bold cyan]privearch@[/bold cyan][bold white]os[/bold white][bold green] ~ $[/bold green]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim cyan]Shutting down Privearch OS. Safe airgap preserved.[/dim cyan]")
            break

        if not user_input:
            continue

        # Handle commands
        if user_input.lower() in ["/exit", "exit", "quit", ":q"]:
            console.print("[dim cyan]Shutting down Privearch OS. Goodbye![/dim cyan]")
            break

        if user_input.lower() in ["/status", "status"]:
            st = kernel.get_system_status()
            for k, v in st.items():
                console.print(f"  [bold cyan]{k}:[/bold cyan] {v}")
            continue

        if user_input.lower() in ["/update", "update", "/ota"]:
            console.print("[cyan]Connecting to OTA update channel...[/cyan]")
            from privearch.updater.cli_updater import run_ota_cli
            run_ota_cli()
            continue

        if user_input.lower() in ["/engine", "/models", "/setup-engine"]:
            from privearch.models.engine_installer import main as engine_setup_main
            engine_setup_main()
            continue

        if user_input.lower().startswith("/scan") or user_input.lower().startswith("/ingest-all"):
            console.print("[cyan]Scanning and ingesting all PDFs in current directory...[/cyan]")
            for f in os.listdir("."):
                if f.lower().endswith(".pdf"):
                    res = kernel.ingest_pdf(f)
                    console.print(f"  [green]✓ {f}:[/green] {res['chunks']} chunks ({res['time_s']}s)")
            console.print(f"[bold green]Index updated. Total chunks in RAM: {kernel.total_chunks}[/bold green]")
            continue

        # Check if input is a PDF path (drag & drop)
        clean_path = user_input.strip('\'"')
        if os.path.exists(clean_path) and clean_path.lower().endswith('.pdf'):
            console.print(f"[bold yellow]📚 Dynamic Ingestion detected PDF: {clean_path}[/bold yellow]")
            with console.status("[cyan]Extracting text, chunking, and computing CPU vector embeddings in RAM...[/cyan]"):
                res = kernel.ingest_pdf(clean_path)
            console.print(f"[bold green]✓ Successfully ingested {res['doc_name']}![/bold green] Pages: {res['pages']}, New Chunks: {res['chunks']}, Total RAM Chunks: {res['total_ram_chunks']} ({res['time_s']}s)\n")
            continue

        # Otherwise treat as a scientific query
        if kernel.total_chunks == 0:
            console.print("[bold red]⚠️ No documents ingested yet.[/bold red] Please drag and drop a PDF into the terminal or run '/scan' to ingest the local chemistry textbooks.")
            continue

        console.print(f"\n[dim cyan]Executing RLCD Operating System Pipeline for: \"{user_input}\"...[/dim cyan]")
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold cyan]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[magenta]Stage 1: Router (0.5B) analyzing risk & entities...", total=None)
            report = kernel.execute_rlcd(user_input)
            progress.update(task, completed=True)

        display_rlcd_report(report)


if __name__ == "__main__":
    if "--setup-engine" in sys.argv or "--engine" in sys.argv:
        from privearch.models.engine_installer import main as engine_setup_main
        engine_setup_main()
    elif "--update" in sys.argv or "-u" in sys.argv:
        from privearch.updater.cli_updater import main as updater_main
        updater_main()
    else:
        run_cli()


