"""Privreach Native Desktop Launcher (Python).

Launches the local background engine and native WinUI 3 Desktop Workstation.
"""

import os
import sys
import time
import socket
import subprocess

def is_port_open(port: int = 8765) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect(("127.0.0.1", port))
            return True
        except OSError:
            return False

def main():
    repo_root = os.path.dirname(os.path.abspath(__file__))
    python_exe = os.path.join(repo_root, "venv", "Scripts", "python.exe")
    server_script = os.path.join(repo_root, "privreach", "desktop_server.py")
    desktop_proj = os.path.join(repo_root, "PrivreachDesktop", "PrivreachDesktop.csproj")

    print("==========================================================")
    print("  PRIVREACH OS - NATIVE FLUENT DESKTOP WORKSTATION v2.0")
    print("==========================================================")

    # 1. Start Server if needed
    if not is_port_open(8765):
        print("[1/2] Starting local REST backend daemon...")
        env = os.environ.copy()
        env["PYTHONPATH"] = repo_root
        subprocess.Popen(
            [python_exe, server_script, "127.0.0.1", "8765"],
            cwd=repo_root,
            env=env,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        time.sleep(2)
    else:
        print("[1/2] Local REST backend engine already active on port 8765.")

    # 2. Launch WinUI 3 App
    try:
        subprocess.run(["taskkill", "/F", "/IM", "PrivreachDesktop.exe"], capture_output=True)
        time.sleep(0.5)
    except Exception:
        pass

    desktop_exe = os.path.join(repo_root, "PrivreachDesktop", "bin", "x64", "Debug", "net8.0-windows10.0.26100.0", "win-x64", "PrivreachDesktop.exe")
    print("[2/2] Launching WinUI 3 Native Desktop Workstation...")
    if os.path.exists(desktop_exe):
        subprocess.Popen([desktop_exe], cwd=os.path.dirname(desktop_exe))
    else:
        subprocess.run(["winapp", "run", desktop_proj, "--detach", "--json"], cwd=repo_root)
    print("[OK] Privreach Workstation launched successfully!")
    print("Zero-Trust Air-Gapped Operation | CPU Embeddings + 4GB VRAM")

if __name__ == "__main__":
    main()
