#!/usr/bin/env python3
"""Deploy Privearch across all existing chemistry PDFs in the folder."""

import os
import sys
import time

# Ensure UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

# Ensure privearch package is imported
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from privearch.config import PrivearchConfig
from privearch.os_engine import PrivearchKernel

console = Console()


def deploy_vault(target_folder: str = "."):
    console.print(Panel(
        "[bold cyan]⚡ PRIVEARCH KNOWLEDGE VAULT DEPLOYMENT[/bold cyan]\n"
        "[white]Indexing all existing scientific chemistry textbooks and chapters in folder.[/white]\n"
        "[dim green]Zero-Trust  •  100% Local  •  In-RAM Persistent Cache[/dim green]",
        border_style="cyan"
    ))

    # 1. Initialize Kernel
    with console.status("[cyan]Initializing Privearch OS Kernel & CPU Embedding Engine...[/cyan]"):
        config = PrivearchConfig()
        kernel = PrivearchKernel(config)

    # 2. Discover PDFs
    pdf_files = []
    for root, _, files in os.walk(target_folder):
        # Ignore cache directory
        if ".privearch_cache" in root:
            continue
        for f in files:
            if f.lower().endswith(".pdf"):
                pdf_files.append(os.path.join(root, f))

    pdf_files.sort()
    console.print(f"[bold yellow]Found {len(pdf_files)} PDF textbook files to deploy.[/bold yellow]\n")

    # 3. Ingest with progress bar
    results = []
    total_start = time.time()

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Ingesting Chemistry PDFs...", total=len(pdf_files))

        for pdf_path in pdf_files:
            file_name = os.path.basename(pdf_path)
            progress.update(task, description=f"[cyan]Ingesting {file_name}...")
            
            res = kernel.ingest_pdf(pdf_path, auto_save=False)
            results.append(res)
            progress.advance(task)

    # 4. Save persistent index
    with console.status("[cyan]Writing In-RAM hybrid vector & BM25 index cache to disk...[/cyan]"):
        kernel.save_index()

    total_time = round(time.time() - total_start, 2)

    # 5. Display Summary Table
    table = Table(title="[bold green]📚 DEPLOYED CHEMISTRY VAULT MANIFEST[/bold green]", border_style="green")
    table.add_column("#", style="dim", width=4)
    table.add_column("PDF Document", style="bold white", width=22)
    table.add_column("Status", style="cyan", width=16)
    table.add_column("Pages", style="white", width=8)
    table.add_column("Chunks", style="yellow", width=8)
    table.add_column("Indexing Time", style="dim white", width=14)

    total_pages = 0
    total_new_chunks = 0
    for idx, r in enumerate(results, start=1):
        pages = r.get("pages", 0)
        chunks = r.get("chunks", 0)
        total_pages += pages
        if r.get("status") == "success":
            total_new_chunks += chunks
            status_text = "[green]✓ Indexed[/green]"
        elif r.get("status") == "already_indexed":
            status_text = "[cyan]✓ Cached[/cyan]"
        else:
            status_text = f"[yellow]{r.get('status')}[/yellow]"

        table.add_row(
            str(idx),
            r.get("doc_name", "unknown"),
            status_text,
            str(pages),
            str(chunks),
            f"{r.get('time_s', 0):.2f}s"
        )

    console.print(table)

    summary_panel = Panel(
        f"[bold white]Deployment Complete in {total_time} seconds![/bold white]\n"
        f"• [bold green]Total Documents:[/bold green] {len(kernel.ingested_files)} PDFs\n"
        f"• [bold green]Total Semantic Chunks in RAM:[/bold green] {kernel.total_chunks} chunks\n"
        f"• [bold green]Total Pages Covered:[/bold green] {total_pages} pages\n"
        f"• [bold green]Persistent Storage:[/bold green] `.privearch_cache/` (Instant ~0.1s reload on next boot)\n\n"
        f"[bold yellow]Ready to Query via:[/bold yellow]\n"
        f"  1. Terminal OS: [cyan]python run_privearch.py[/cyan]\n"
        f"  2. Web Console: [cyan]python run_web.py[/cyan] (http://127.0.0.1:7860)",
        title="[bold green]✅ VAULT READY FOR ZERO-HALLUCINATION SYNTHESIS[/bold green]",
        border_style="green"
    )
    console.print(summary_panel)


if __name__ == "__main__":
    deploy_vault(".")
