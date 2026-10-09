"""Interactive CLI OTA Updater for Privearch."""

import os
import sys
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, DownloadColumn, TransferSpeedColumn
from rich.prompt import Confirm, Prompt

from privearch.updater.version import VERSION, BUILD_CHANNEL, RELEASE_DATE, DEFAULT_OTA_MANIFEST_URL
from privearch.updater.ota_manager import OTAManager

# Ensure UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console()


def run_ota_cli(manifest_url: str = DEFAULT_OTA_MANIFEST_URL, check_only: bool = False, force: bool = False):
    """Run interactive OTA Update check and installation."""
    app_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    manager = OTAManager(current_version=VERSION, manifest_url=manifest_url, install_dir=app_dir)

    console.print(Panel(
        f"[bold white]Privearch OTA Update Center[/bold white]\n"
        f"[cyan]Current Installed Version:[/cyan] [bold green]v{VERSION}[/bold green] ({BUILD_CHANNEL})\n"
        f"[cyan]Release Date:[/cyan] {RELEASE_DATE}\n"
        f"[cyan]Manifest Source:[/cyan] [dim]{manifest_url}[/dim]\n"
        f"[cyan]Install Root:[/cyan] [dim]{app_dir}[/dim]",
        title="[bold cyan]🔄 OVER-THE-AIR (OTA) UPDATER[/bold cyan]",
        border_style="cyan"
    ))

    with console.status("[cyan]Connecting to update channel and checking manifest...[/cyan]"):
        has_update, manifest, msg = manager.check_for_updates()

    if not manifest:
        console.print(f"[bold red]✗ Update Check Failed:[/bold red] {msg}\n")
        return False

    table = Table(title="[bold yellow]VERSION STATUS[/bold yellow]", border_style="yellow")
    table.add_column("Property", style="bold white", width=22)
    table.add_column("Details", style="green")

    table.add_row("Current Version", f"v{VERSION}")
    table.add_row("Channel Latest", f"v{manifest.get('version', 'Unknown')}")
    table.add_row("Release Date", str(manifest.get('release_date', 'Unknown')))
    table.add_row("Min Compatible", str(manifest.get('min_compatible_version', '1.0.0')))
    table.add_row("Update Status", f"[bold green]UPDATE AVAILABLE[/bold green]" if has_update else "[bold cyan]UP TO DATE[/bold cyan]")
    console.print(table)

    if "changelog" in manifest and manifest["changelog"]:
        console.print(Panel(
            manifest["changelog"],
            title=f"[bold green]📝 What's New in v{manifest.get('version')}[/bold green]",
            border_style="green"
        ))

    if check_only:
        return has_update

    if not has_update and not force:
        console.print("\n[bold green]✓ Your Privearch installation is already on the latest version.[/bold green]\n")
        return True

    if not Confirm.ask("[bold yellow]Do you want to download and apply this update now?[/bold yellow]", default=True):
        console.print("[dim]Update skipped by user.[/dim]")
        return False

    console.print()
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Downloading update package...", total=100)

        def cb(fraction):
            progress.update(task, completed=fraction * 100)

        success, zip_or_err = manager.download_update(manifest, progress_cb=cb)

    if not success:
        console.print(f"[bold red]✗ Download / Verification Failed:[/bold red] {zip_or_err}")
        return False

    console.print("[bold green]✓ Package downloaded and SHA-256 cryptographic signature verified![/bold green]")
    console.print("[cyan]Backing up current installation and atomically applying update (preserving .privearch_cache/)...[/cyan]")

    with console.status("[yellow]Applying update and updating local components...[/yellow]"):
        app_success, app_msg = manager.apply_update(zip_or_err)

    if not app_success:
        console.print(f"[bold red]✗ Update Application Failed:[/bold red] {app_msg}")
        return False

    console.print(f"[bold green]✓ {app_msg}[/bold green]")
    console.print(Panel(
        "[bold green]Update successfully installed![/bold green]\n"
        "Your offline knowledge vault (.privearch_cache/) and user data were preserved.\n"
        "Please restart Privearch to use the new features.",
        title="[bold green]🎉 UPDATE COMPLETE[/bold green]",
        border_style="green"
    ))
    return True


def main():
    parser = argparse.ArgumentParser(description="Privearch Over-The-Air (OTA) Updater")
    parser.add_argument("--update", "-u", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--url", default=DEFAULT_OTA_MANIFEST_URL, help="Custom OTA manifest URL or local file path")
    parser.add_argument("--check", action="store_true", help="Only check for updates without installing")
    parser.add_argument("--force", action="store_true", help="Force reinstall/update even if already on latest version")
    parser.add_argument("--rollback", action="store_true", help="Rollback to previous version from safety backup")

    args = parser.parse_args()

    if args.rollback:
        app_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        mgr = OTAManager(install_dir=app_dir)
        console.print("[yellow]Attempting rollback to previous backup...[/yellow]")
        ok, msg = mgr.rollback()
        if ok:
            console.print(f"[bold green]✓ {msg}[/bold green]")
        else:
            console.print(f"[bold red]✗ {msg}[/bold red]")
        sys.exit(0 if ok else 1)

    run_ota_cli(manifest_url=args.url, check_only=args.check, force=args.force)


if __name__ == "__main__":
    main()
