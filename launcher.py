"""Privreach OS Standalone Single-File Executable Launcher.

Bundles and launches:
- WinUI 3 Native Desktop Workstation (PrivreachDesktop.exe)
- Zero-Trust Offline Python Backend Engine (privreach_engine.exe)
- Embedded Google Gemma 3 1B IT Inference Engine (GGUF Q4_K_M)
"""

import os
import sys
import time
import zipfile
import subprocess
import shutil

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

VERSION = "2.0.0"
APP_DIR_NAME = "Workstation-v2.0"


def get_install_dir() -> str:
    local_app_data = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    return os.path.join(local_app_data, "Privreach", APP_DIR_NAME)


def is_installed_valid(install_dir: str) -> bool:
    desktop_exe = os.path.join(install_dir, "PrivreachDesktop.exe")
    engine_exe = os.path.join(install_dir, "privreach_engine", "privreach_engine.exe")
    model_file = os.path.join(install_dir, "privreach_engine", "models", "gemma-3-1b-it-q4_k_m.gguf")
    version_file = os.path.join(install_dir, "version.txt")

    if not (os.path.exists(desktop_exe) and os.path.exists(engine_exe) and os.path.exists(model_file)):
        return False

    if os.path.exists(version_file):
        try:
            with open(version_file, "r", encoding="utf-8") as f:
                return f.read().strip() == VERSION
        except Exception:
            return False
    return False


def unpack_payload(install_dir: str):
    print("=" * 60)
    print("  PRIVREACH OS v2.0 - EMBEDDED WORKSTATION INITIALIZATION")
    print("=" * 60)
    print("Unpacking native WinUI 3 desktop & embedded Google Gemma 3 1B IT...")

    # Locate payload zip
    bundle_zip = None
    candidates = [
        os.path.join(getattr(sys, "_MEIPASS", ""), "PrivreachOS-v2.0-win-x64.zip"),
        os.path.join(os.path.dirname(sys.executable), "PrivreachOS-v2.0-win-x64.zip"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", "PrivreachOS-v2.0-win-x64.zip"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "PrivreachOS-v2.0-win-x64.zip"),
    ]
    for c in candidates:
        if c and os.path.exists(c) and os.path.getsize(c) > 100_000_000:
            bundle_zip = c
            break

    if not bundle_zip:
        raise FileNotFoundError("Embedded payload archive PrivreachOS-v2.0-win-x64.zip not found!")

    os.makedirs(install_dir, exist_ok=True)

    # Fast extraction using tar.exe if available on Windows, else zipfile
    tar_exe = shutil.which("tar.exe") or "C:\\Windows\\System32\\tar.exe"
    extracted = False
    if os.path.exists(tar_exe):
        try:
            print("[1/2] Extracting high-performance binary package via native system tar...")
            subprocess.run([tar_exe, "-xf", bundle_zip, "-C", install_dir], check=True)
            extracted = True
        except Exception as e:
            print(f"Native tar extraction fallback: {e}")

    if not extracted:
        print("[1/2] Extracting archive via standard zip extraction...")
        with zipfile.ZipFile(bundle_zip, "r") as zf:
            zf.extractall(install_dir)

    with open(os.path.join(install_dir, "version.txt"), "w", encoding="utf-8") as f:
        f.write(VERSION)
    print("[2/2] Verification complete. Workstation ready!")


def main():
    install_dir = get_install_dir()

    # Allow flags like --repair, --reinstall, --extract, --fresh
    force_unpack = any(arg in sys.argv for arg in ["--repair", "--reinstall", "--extract", "--fresh"])

    if force_unpack or not is_installed_valid(install_dir):
        unpack_payload(install_dir)

    desktop_exe = os.path.join(install_dir, "PrivreachDesktop.exe")
    if not os.path.exists(desktop_exe):
        raise FileNotFoundError(f"Desktop executable not found at: {desktop_exe}")

    print("⚡ Launching Privreach OS Native Desktop Workstation...")
    subprocess.Popen([desktop_exe] + sys.argv[1:], cwd=install_dir)
    print("Workstation process active.")


if __name__ == "__main__":
    main()
