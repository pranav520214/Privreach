import sys
import io
import os
from pathlib import Path
from huggingface_hub import hf_hub_download
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

sys.path.append(str(Path(__file__).parent))

from core.orchestration.pipeline import PrvaVedaPipeline

console = Console()

def get_model_paths():
    with console.status("[bold yellow]Locating local GGUF models...", spinner="dots"):
        synth_path = hf_hub_download(repo_id="mradermacher/Huihui-Qwen3.5-4B-abliterated-GGUF", filename="Huihui-Qwen3.5-4B-abliterated.Q4_K_M.gguf")
        router_path = hf_hub_download(repo_id="Qwen/Qwen2.5-0.5B-Instruct-GGUF", filename="qwen2.5-0.5b-instruct-q4_k_m.gguf")
    return synth_path, router_path

def main():
    console.print(Panel.fit("[bold cyan]Prva Veda - Critical Research Mode[/bold cyan]\nLocal SLM System (Phase 8 Dual-Architecture)", border_style="cyan"))
    
    corpus_path = r"E:\Prva_Veda_Research_Library\datasets\retrieval\chunks.jsonl"
    synth_path, router_path = get_model_paths()
            
    with console.status("[bold yellow]Loading Dual-Model System into memory...", spinner="dots"):
        pipeline = PrvaVedaPipeline(synth_model_path=synth_path, router_model_path=router_path, corpus_path=corpus_path)
    
    console.print("[bold green]System Ready.[/bold green]\n")
    
    while True:
        console.print("\n[bold cyan]--- Main Menu ---[/bold cyan]")
        console.print("1. [bold yellow]Ingest PDF[/bold yellow] (Type '1')")
        console.print("2. [bold magenta]Enter Chat Mode[/bold magenta] (Type '2')")
        console.print("3. [bold red]Exit[/bold red] (Type '3')")
        
        choice = Prompt.ask("Select an option")
        
        if choice == '1':
            pdf_path = Prompt.ask("[bold yellow]Drag and drop a PDF file here (or paste the full path)[/bold yellow]").strip()
            # Strip quotes if dragged in terminal
            pdf_path = pdf_path.strip('"').strip("'")
            
            if not os.path.exists(pdf_path):
                console.print(f"[bold red]Error: File not found at {pdf_path}[/bold red]")
                continue
                
            with console.status(f"[bold yellow]Ingesting {Path(pdf_path).name}...", spinner="bouncingBar"):
                chunks_added = pipeline.ingest_pdf(pdf_path)
            console.print(f"[bold green]Success! {chunks_added} chunks dynamically added to the live index.[/bold green]")
            
        elif choice == '2':
            console.print("\n[bold magenta]--- Chat Mode ---[/bold magenta] (Type 'back' to return to menu)")
            while True:
                try:
                    query = Prompt.ask("\n[bold magenta]User[/bold magenta]")
                    if query.lower() in ['back', 'exit', 'quit']:
                        break
                    if not query.strip():
                        continue
                        
                    console.print("\n[bold cyan]Prva Veda System[/bold cyan]")
                    
                    class StreamCatcher:
                        def __call__(self, msg):
                            if "===" in msg: return
                            if "[RLCD]" in msg:
                                console.print(f"[dim blue]{msg}[/dim blue]")
                            elif "[KNOWLEDGE]" in msg:
                                console.print(f"[dim yellow]{msg}[/dim yellow]")
                            elif "[SLM]" in msg:
                                console.print(f"[dim magenta]{msg}[/dim magenta]")
                            elif "[VERIFIER]" in msg:
                                console.print(f"[dim red]{msg}[/dim red]")
                            elif msg.strip():
                                console.print(f"[dim]{msg}[/dim]")
                    
                    with console.status("[bold green]Processing via Dual-Model Pipeline...", spinner="bouncingBar"):
                        candidate, report, plan = pipeline.execute(query, stream_callback=StreamCatcher())
                    
                    console.print("\n[bold green]Final Response:[/bold green]")
                    console.print(Panel(Markdown(candidate), title=f"Risk Level: {plan.risk_level.value.upper()}", border_style="green"))
                    
                    if report and not report.is_safe:
                        console.print("\n[bold red]⚠️ ADVERSARIAL VERIFIER WARNING ⚠️[/bold red]")
                        for claim in report.claims:
                            if claim.verdict != "SUPPORTED":
                                console.print(f"[red]• Claim:[/red] {claim.claim_text}")
                                console.print(f"[red]  Verdict:[/red] {claim.verdict}")
                                console.print(f"[red]  Reasoning:[/red] {claim.reasoning}")
                                
                except KeyboardInterrupt:
                    break
                    
        elif choice == '3' or choice.lower() in ['exit', 'quit']:
            console.print("[bold green]Shutting down Prva Veda...[/bold green]")
            break
        else:
            console.print("[bold red]Invalid choice. Please select 1, 2, or 3.[/bold red]")

if __name__ == "__main__":
    main()
