"""Zero-Friction Automated AI Engine Bootstrapper for Privearch.

Automatically detects, downloads, installs, starts Ollama, and pulls
required local LLMs (Qwen2.5 0.5B + 3B) without requiring manual setup.
Also supports portable llama.cpp runtimes for 100% free offline use.
"""

import os
import sys
import time
import json
import shutil
import tempfile
import subprocess
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional, Callable, Tuple

OLLAMA_WIN_INSTALLER_URL = "https://ollama.com/download/OllamaSetup.exe"
DEFAULT_REQUIRED_MODELS = ["qwen2.5:0.5b", "qwen2.5-coder:3b"]


def is_engine_running(port: int = 11434) -> bool:
    """Check if local inference engine (Ollama or llama-server) is responding."""
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/api/tags")
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status == 200
    except Exception:
        # Also check OpenAI-compatible /v1/models endpoint for llama-server
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{port}/v1/models")
            with urllib.request.urlopen(req, timeout=2) as resp:
                return resp.status == 200
        except Exception:
            return False


def find_ollama_executable() -> Optional[str]:
    """Locate ollama.exe on PATH or standard Windows installation locations."""
    # 1. System PATH
    found = shutil.which("ollama")
    if found and os.path.exists(found):
        return found

    # 2. LocalAppData
    local_app_data = os.getenv("LOCALAPPDATA", "")
    if local_app_data:
        p1 = os.path.join(local_app_data, "Programs", "Ollama", "ollama.exe")
        if os.path.exists(p1):
            return p1

    # 3. Program Files
    prog_files = os.getenv("ProgramFiles", "C:\\Program Files")
    p2 = os.path.join(prog_files, "Ollama", "ollama.exe")
    if os.path.exists(p2):
        return p2

    return None


def start_ollama_daemon() -> bool:
    """Start the background Ollama daemon if not already running."""
    if is_engine_running(11434):
        return True

    ollama_exe = find_ollama_executable()
    if not ollama_exe:
        return False

    try:
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        subprocess.Popen(
            [ollama_exe, "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=flags
        )
        for _ in range(12):
            time.sleep(0.5)
            if is_engine_running(11434):
                return True
    except Exception:
        pass

    return is_engine_running(11434)


def download_ollama_installer(
    dest_path: Optional[str] = None,
    progress_cb: Optional[Callable[[float, str], None]] = None
) -> str:
    """Download official OllamaSetup.exe for Windows."""
    if not dest_path:
        dest_path = os.path.join(tempfile.gettempdir(), "OllamaSetup.exe")

    req = urllib.request.Request(
        OLLAMA_WIN_INSTALLER_URL,
        headers={"User-Agent": "Privearch-Engine-Installer/1.0.0"}
    )

    with urllib.request.urlopen(req, timeout=60) as resp, open(dest_path, "wb") as out:
        total_header = resp.getheader("content-length")
        total_size = int(total_header) if total_header else 0
        downloaded = 0
        chunk_size = 65536

        while True:
            chunk = resp.read(chunk_size)
            if not chunk:
                break
            out.write(chunk)
            downloaded += len(chunk)
            if progress_cb and total_size > 0:
                fraction = min(1.0, downloaded / total_size)
                progress_cb(fraction, f"Downloading Ollama engine: {downloaded / (1024*1024):.1f} / {total_size / (1024*1024):.1f} MB")

    return dest_path


def install_ollama(
    silent: bool = True,
    progress_cb: Optional[Callable[[float, str], None]] = None
) -> Tuple[bool, str]:
    """Download and execute Ollama installer."""
    if find_ollama_executable():
        start_ollama_daemon()
        return True, "Ollama is already installed and running."

    try:
        if progress_cb:
            progress_cb(0.1, "Connecting to official Ollama download server...")
        installer_path = download_ollama_installer(progress_cb=progress_cb)

        if progress_cb:
            progress_cb(0.9, "Executing Ollama setup wizard...")

        cmd = [installer_path]
        if silent:
            cmd.extend(["/SILENT", "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"])

        proc = subprocess.run(cmd, timeout=300)
        time.sleep(2.0)

        ollama_bin = find_ollama_executable()
        if not ollama_bin:
            return False, "Ollama installer finished, but ollama.exe was not detected."

        # Start daemon
        started = start_ollama_daemon()
        if not started:
            return False, "Ollama installed, but failed to bind background daemon."

        return True, "Ollama successfully installed and started!"

    except Exception as e:
        return False, f"Failed to install Ollama: {e}"


def list_installed_models() -> List[str]:
    """Retrieve list of model names currently in Ollama."""
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/api/tags")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return [m.get("name", "") for m in data.get("models", [])]
    except Exception:
        return []


def pull_model(
    model_name: str,
    progress_cb: Optional[Callable[[float, str], None]] = None
) -> Tuple[bool, str]:
    """
    Pull model using Ollama streaming API with real-time progress callbacks.
    """
    if not start_ollama_daemon():
        return False, "Ollama service is not running."

    url = "http://127.0.0.1:11434/api/pull"
    payload = json.dumps({"name": model_name}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=1200) as resp:
            for line in resp:
                if not line:
                    continue
                try:
                    chunk = json.loads(line.decode("utf-8"))
                    status = chunk.get("status", "")
                    completed = chunk.get("completed", 0)
                    total = chunk.get("total", 0)

                    if progress_cb:
                        if total > 0:
                            fraction = completed / total
                            progress_cb(fraction, f"Pulling {model_name} [{status}]: {completed/(1024*1024):.1f}/{total/(1024*1024):.1f} MB")
                        else:
                            progress_cb(0.5, f"Pulling {model_name}: {status}...")
                except Exception:
                    continue

        return True, f"Successfully pulled {model_name}"
    except Exception as e:
        return False, f"Failed to pull {model_name}: {e}"


def ensure_required_models(
    models: Optional[List[str]] = None,
    progress_cb: Optional[Callable[[float, str], None]] = None
) -> Tuple[bool, List[str]]:
    """Verify that required models exist; auto-pull any that are missing."""
    target_models = models or DEFAULT_REQUIRED_MODELS
    installed = list_installed_models()

    pulled = []
    for model in target_models:
        # Check if already present (e.g. 'qwen2.5:0.5b' in 'qwen2.5:0.5b' or 'qwen2.5:0.5b-instruct')
        has_model = any(model in m or m in model for m in installed)
        if not has_model:
            if progress_cb:
                progress_cb(0.0, f"Model '{model}' not found. Starting automatic download...")
            ok, msg = pull_model(model, progress_cb=progress_cb)
            if not ok:
                return False, [f"Failed to pull {model}: {msg}"]
            pulled.append(model)

    return True, pulled


def bootstrap_system(
    models: Optional[List[str]] = None,
    silent: bool = False,
    progress_cb: Optional[Callable[[float, str], None]] = None
) -> Tuple[bool, str]:
    """
    Master 1-click self-install bootstrapper:
    1. Checks if Ollama is running.
    2. If not installed, downloads and installs Ollama automatically.
    3. Starts Ollama daemon.
    4. Downloads required models (qwen2.5:0.5b and qwen2.5-coder:3b) automatically.
    """
    # Step 1: Ensure engine executable
    ollama_bin = find_ollama_executable()
    if not ollama_bin:
        if progress_cb:
            progress_cb(0.05, "Ollama engine not detected. Installing Ollama for Windows...")
        ok, msg = install_ollama(silent=silent, progress_cb=progress_cb)
        if not ok:
            return False, msg

    # Step 2: Ensure daemon active
    if not start_ollama_daemon():
        return False, "Could not start local Ollama background service."

    # Step 3: Ensure models downloaded
    models_to_pull = models or DEFAULT_REQUIRED_MODELS
    ok_models, pulled = ensure_required_models(models_to_pull, progress_cb=progress_cb)
    if not ok_models:
        return False, f"Model provisioning failed: {pulled}"

    return True, "Local AI Engine is 100% installed, running, and ready for zero-trust inference!"


# CLI interactive runner
def main():
    import argparse
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, DownloadColumn, TransferSpeedColumn
    from rich.prompt import Confirm

    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    console = Console()
    parser = argparse.ArgumentParser(description="Privearch Local AI Engine Auto-Installer")
    parser.add_argument("--auto", action="store_true", help="Run unattended automatic installation")
    parser.add_argument("--models-only", action="store_true", help="Only pull missing models")
    args = parser.parse_args()

    console.print(Panel(
        "[bold white]Privearch Zero-Friction Engine Setup[/bold white]\n"
        "[cyan]Configures local Ollama inference service and required models.[/cyan]\n"
        "[green]100% Free & Local • No Cloud Keys Required • CPU + GPU Support[/green]",
        title="[bold cyan]⚡ AI ENGINE INSTALLER[/bold cyan]",
        border_style="cyan"
    ))

    running = is_engine_running()
    ollama_path = find_ollama_executable()
    installed_models = list_installed_models() if running else []

    color = "green" if running else "yellow"
    status_str = "Running (Port 11434)" if running else "Stopped"
    console.print(f"  • Ollama Executable: [bold]{ollama_path or 'Not Installed'}[/bold]")
    console.print(f"  • Service Status:    [{color}]{status_str}[/{color}]")
    console.print(f"  • Installed Models:  [dim]{', '.join(installed_models) if installed_models else 'None'}[/dim]\n")

    if not args.auto:
        if not Confirm.ask("[bold yellow]Proceed with automatic installation and model setup?[/bold yellow]", default=True):
            console.print("[dim]Setup cancelled by user.[/dim]")
            sys.exit(0)

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Initializing local engine...", total=100)

        def cb(frac, msg):
            progress.update(task, completed=int(frac * 100), description=f"[cyan]{msg}")

        ok, msg = bootstrap_system(silent=True, progress_cb=cb)
        progress.update(task, completed=100, description="[bold green]AI Engine Setup Complete!")

    if ok:
        console.print(Panel(
            f"[bold green]✓ {msg}[/bold green]\n\n"
            f"[white]Active Models:[/white] [cyan]{', '.join(list_installed_models())}[/cyan]\n"
            f"[white]Inference Endpoint:[/white] [dim]http://127.0.0.1:11434[/dim]\n\n"
            f"[bold cyan]Privearch is now ready to synthesize and audit research with zero external dependencies![/bold cyan]",
            title="[bold green]🎉 ENGINE READY[/bold green]",
            border_style="green"
        ))
    else:
        console.print(f"[bold red]✗ Setup encountered an error:[/bold red] {msg}")
        sys.exit(1)


if __name__ == "__main__":
    main()
