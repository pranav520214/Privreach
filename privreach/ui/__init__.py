"""Privearch UI Module: Three-Plane Research Workstation and Explainer Canvas."""

import os
import sys
import socket
from privearch.config import PrivearchConfig
from privearch.os_engine import PrivearchKernel
from privearch.ui.canvas_protocol import CanvasPayload, CanvasViewType
from privearch.ui.canvas_generator import CanvasGenerator
try:
    from privearch.ui.three_plane_app import build_three_plane_app
except ImportError:
    build_three_plane_app = None



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


def launch_three_plane_web(port: int = 7860, share: bool = False):
    """Launches the Three-Plane Research Operating Environment on localhost."""
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    config = PrivearchConfig()
    kernel = PrivearchKernel(config)
    st = kernel.get_system_status()
    print(f"[OK] Privreach Three-Plane Workstation initialized with {st['indexed_chunks']} chunks in RAM.")

    app = build_three_plane_app(kernel=kernel)
    target_port = find_available_port(start_port=port)
    print(f"[OK] Serving Privreach Operating Environment at http://127.0.0.1:{target_port}")

    app.launch(
        server_name="127.0.0.1",
        server_port=target_port,
        share=share,
        inbrowser=True,
        show_error=True
    )


__all__ = [
    "build_three_plane_app",
    "launch_three_plane_web",
    "CanvasGenerator",
    "CanvasPayload",
    "CanvasViewType",
]
