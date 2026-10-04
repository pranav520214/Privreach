#!/usr/bin/env python3
"""Entry point for Privearch Terminal OS."""

import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from privearch.cli import run_cli

if __name__ == "__main__":
    run_cli()
