"""Command-line interface for the Privreach OS Modern Patching & Updation System."""

import os
import sys
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm

from privreach.updater.updater_service import get_updater_service
from privreach.updater.patch_builder import PatchBuilder
from privreach.updater.version import VERSION, BUILD_CHANNEL, RELEASE_DATE

console = Console()


def display_status():
    service = get_updater_service()
    st = service.get_status()

    table = Table(title="[bold cyan]PRIVREACH OS UPDATER STATUS[/bold cyan]", border_style="cyan")
    table.add_column("Property", style="bold white", width=20)
    table.add_column("Value", style="green")

    table.add_row("Installed Version", f"v{st['version']} ({st['channel']})")
    table.add_row("Release Date", st["release_date"])
    table.add_row("Git Commit", st["git_commit"])
    table.add_row("Python", st["python_version"])
    table.add_row("Total Snapshots", str(st["total_snapshots"]))
    table.add_row("Latest Snapshot", str(st["latest_snapshot"] or "None"))
    table.add_row("Can Rollback", "[bold green]YES[/bold green]" if st["can_rollback"] else "[dim]NO[/dim]")

    console.print(table)


def check_updates():
    service = get_updater_service()
    with console.status("[cyan]Checking for OTA updates...[/cyan]"):
        res = service.check_for_updates()

    if res.has_update:
        console.print(Panel(
            f"[bold green]✓ Update Available: v{res.latest_version}[/bold green]\n"
            f"Channel: {res.channel}\n"
            f"Changelog:\n{res.changelog or 'Bug fixes and performance enhancements.'}",
            title="[bold yellow]NEW RELEASE[/bold yellow]",
            border_style="green"
        ))
    else:
        console.print(f"[bold green]✓ {res.message}[/bold green]")


def list_snapshots():
    service = get_updater_service()
    snaps = service.list_snapshots()

    if not snaps:
        console.print("[yellow]No snapshots found.[/yellow]")
        return

    table = Table(title="[bold yellow]ROLLBACK SNAPSHOTS[/bold yellow]", border_style="yellow")
    table.add_column("Snapshot ID", style="bold white")
    table.add_column("Version", style="cyan")
    table.add_column("Reason", style="magenta")
    table.add_column("Files Backed Up", justify="right")

    for s in snaps:
        table.add_row(s.snapshot_id, s.version, s.reason, str(len(s.affected_files)))

    console.print(table)


def apply_patch(patch_file: str):
    service = get_updater_service()
    if not os.path.exists(patch_file):
        console.print(f"[bold red]Error: Patch file '{patch_file}' does not exist.[/bold red]")
        return

    console.print(f"[cyan]Applying patch bundle: {patch_file}...[/cyan]")
    res = service.apply_patch_file(patch_file, auto_rollback=True)

    if res.success:
        console.print(Panel(
            f"[bold green]✓ Patch Applied Successfully![/bold green]\n"
            f"Patch ID: {res.patch_id}\n"
            f"Target Version: v{res.target_version}\n"
            f"Files Modified: {len(res.files_modified)}\n"
            f"Modules Hot-Reloaded: {len(res.hot_reloaded_modules)}\n"
            f"Snapshot ID: {res.snapshot_id}",
            title="[bold green]PATCH SUCCESS[/bold green]",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"[bold red]✗ Patch Application Failed:[/bold red]\n{res.message}\n"
            f"Error: {res.error}",
            title="[bold red]PATCH ERROR[/bold red]",
            border_style="red"
        ))


def rollback(snapshot_id: str = None):
    service = get_updater_service()
    console.print(f"[yellow]Initiating atomic rollback...[/yellow]")
    res = service.rollback_to_snapshot(snapshot_id)

    if res.success:
        console.print(f"[bold green]✓ {res.message}[/bold green]")
        for f in res.restored_files:
            console.print(f"  [dim]• Restored: {f}[/dim]")
    else:
        console.print(f"[bold red]✗ Rollback failed: {res.message}[/bold red]")


def build_patch_cmd(patch_id: str, title: str, files: list, output: str):
    builder = PatchBuilder()
    manifest = builder.build_patch(
        patch_id=patch_id,
        title=title,
        description="CLI Generated Patch",
        target_version="2.0.1",
        file_paths=files
    )
    bundle_path = builder.export_patch_bundle(manifest, output)
    console.print(f"[bold green]✓ Patch bundle compiled: {bundle_path}[/bold green]")


def main():
    parser = argparse.ArgumentParser(description="Privreach OS Modern Updation & Patch System")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("status", help="Show version telemetry and snapshot count")
    subparsers.add_parser("check", help="Check for available OTA updates")
    subparsers.add_parser("snapshots", help="List point-in-time snapshots")

    apply_parser = subparsers.add_parser("apply", help="Apply a .privpatch bundle")
    apply_parser.add_argument("patch_file", help="Path to .privpatch file")

    rb_parser = subparsers.add_parser("rollback", help="Revert to snapshot")
    rb_parser.add_argument("snapshot_id", nargs="?", default=None, help="Specific snapshot ID (default: latest)")

    build_parser = subparsers.add_parser("build", help="Build a .privpatch bundle")
    build_parser.add_argument("--id", required=True, help="Patch ID")
    build_parser.add_argument("--title", required=True, help="Patch Title")
    build_parser.add_argument("--output", "-o", default="update.privpatch", help="Output file")
    build_parser.add_argument("files", nargs="+", help="Files to include in patch")

    args = parser.parse_args()

    if args.command == "status" or not args.command:
        display_status()
    elif args.command == "check":
        check_updates()
    elif args.command == "snapshots":
        list_snapshots()
    elif args.command == "apply":
        apply_patch(args.patch_file)
    elif args.command == "rollback":
        rollback(args.snapshot_id)
    elif args.command == "build":
        build_patch_cmd(args.id, args.title, args.files, args.output)


if __name__ == "__main__":
    main()
