#!/usr/bin/env python3
"""Entry point for Privearch Web Dashboard."""

import sys
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from privearch.web_ui import launch_web

if __name__ == "__main__":
    launch_web(port=7860)
