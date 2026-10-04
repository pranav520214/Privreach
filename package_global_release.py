"""Package Privearch Global Standalone Installer & OTA Release Bundle."""

import os
import sys
import json
import shutil
import zipfile

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from privearch.updater.version import VERSION, RELEASE_DATE
from privearch.updater.ota_manager import calculate_sha256


def build_global_release():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    dist_dir = os.path.join(base_dir, "dist")
    os.makedirs(dist_dir, exist_ok=True)

    print("=" * 70)
    print(f"  BUILDING PRIVEARCH GLOBAL RELEASE v{VERSION}")
    print("=" * 70)

    # 1. Build Standalone Portable Distribution Directory
    portable_dir = os.path.join(dist_dir, f"Privearch-v{VERSION}-Windows")
    if os.path.exists(portable_dir):
        shutil.rmtree(portable_dir)
    os.makedirs(portable_dir, exist_ok=True)

    # Include items
    files_to_copy = [
        "Privearch-Setup.exe",
        "Privearch.exe",
        "Privearch-Terminal.exe",
        "privearch.ico",
        "run_web.py",
        "run_privearch.py",
        "deploy_chemistry_vault.py",
        "start_privearch_web.bat",
        "start_privearch_cli.bat",
        "README.md"
    ]

    for f in files_to_copy:
        src = os.path.join(base_dir, f)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(portable_dir, f))
            print(f"  ✓ Copied {f}")

    # Copy privearch package
    privearch_dst = os.path.join(portable_dir, "privearch")
    shutil.copytree(os.path.join(base_dir, "privearch"), privearch_dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    print("  ✓ Copied privearch engine package")

    # Copy pre-indexed chemistry knowledge vault
    cache_src = os.path.join(base_dir, ".privearch_cache")
    if os.path.exists(cache_src):
        cache_dst = os.path.join(portable_dir, ".privearch_cache")
        shutil.copytree(cache_src, cache_dst)
        print("  ✓ Copied pre-indexed Chemistry Vault (.privearch_cache, 2,280 chunks)")

    # 2. Create Global Installer / Portable Zip
    zip_path = os.path.join(dist_dir, f"Privearch-v{VERSION}-Windows-x64.zip")
    print(f"\nCreating global distribution archive: {os.path.basename(zip_path)}...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(portable_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, dist_dir)
                zf.write(full_path, rel_path)

    zip_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    zip_sha = calculate_sha256(zip_path)
    print(f"  ✓ Archive created: {zip_size_mb:.2f} MB")
    print(f"  ✓ SHA-256: {zip_sha}")

    # 3. Create Official OTA Update Bundle (without .privearch_cache so user data is never overwritten)
    ota_zip_path = os.path.join(dist_dir, f"privearch-ota-v{VERSION}.zip")
    print(f"\nCreating official OTA update payload: {os.path.basename(ota_zip_path)}...")
    with zipfile.ZipFile(ota_zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Include engine, executables, scripts
        for item in ["privearch", "Privearch.exe", "Privearch-Terminal.exe", "privearch.ico", "run_web.py", "run_privearch.py", "deploy_chemistry_vault.py", "README.md"]:
            src = os.path.join(base_dir, item)
            if os.path.isdir(src):
                for root, _, files in os.walk(src):
                    if "__pycache__" in root:
                        continue
                    for file in files:
                        fp = os.path.join(root, file)
                        rp = os.path.relpath(fp, base_dir)
                        zf.write(fp, rp)
            elif os.path.isfile(src):
                zf.write(src, item)

    ota_size_mb = os.path.getsize(ota_zip_path) / (1024 * 1024)
    ota_sha = calculate_sha256(ota_zip_path)
    print(f"  ✓ OTA Payload created: {ota_size_mb:.2f} MB")
    print(f"  ✓ OTA SHA-256: {ota_sha}")

    # 4. Generate version.json manifest
    manifest = {
        "version": VERSION,
        "release_date": RELEASE_DATE,
        "channel": "stable",
        "min_compatible_version": "1.0.0",
        "changelog": (
            "### Privearch v1.2.0 Release - Three-Plane Operating Environment & Explainer Canvas\n"
            "- Three-Plane Research Workstation: Left (Chat & Intent), Center (Explainer Canvas), Right (Media & Vault), Bottom (Execution Console)\n"
            "- Explainer Canvas: Interactive Plotly scientific curves, step-by-step KaTeX derivations, real-time HTML5 particle simulation, adversarial claims inspector\n"
            "- Execution Console: Live terminal-like logs, model latency, memory telemetry, and Run/Stop/Rebuild controls\n"
            "- Deterministic Scientific Compute: Non-hallucinatory SymPy and NumPy mathematical solver\n"
            "- Tool Graph Architecture: Extensible BaseToolAdapter and PythonSandboxAdapter with AST security auditing\n"
            "- Artifact Registry & Provenance Ledger: Complete backward provenance tracking\n"
            "- Dual-Model Brain-Trust (0.5B Router + 4B Synthesizer + 0.5B Verifier)\n"
            "- 100% Local Airgap (Zero Cloud Compute, CPU embeddings + 4GB VRAM)"
        ),
        "download_url": f"https://github.com/pranav520214/Privreach/releases/download/v{VERSION}/privearch-ota-v{VERSION}.zip",


        "sha256": ota_sha
    }

    manifest_path = os.path.join(dist_dir, "version.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"  ✓ OTA Manifest generated: {os.path.basename(manifest_path)}")

    # Also copy version.json to root for easy local hosting / testing
    shutil.copy2(manifest_path, os.path.join(base_dir, "version.json"))

    print("\n" + "=" * 70)
    print("🎉 GLOBAL DISTRIBUTION & OTA PACKAGING COMPLETE!")
    print(f"Outputs located in: {dist_dir}")
    print("=" * 70)


if __name__ == "__main__":
    build_global_release()
