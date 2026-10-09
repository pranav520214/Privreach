"""Privearch / Privreach OS Version and Build Metadata (v2.0 Modern Architecture)."""

import os
import sys
import subprocess
from typing import Dict, Any

VERSION = "2.0.0"
BUILD_CHANNEL = "stable"  # "stable", "beta", "hotfix"
RELEASE_DATE = "2026-10-09"
MIN_COMPATIBLE_VERSION = "1.0.0"
DEFAULT_OTA_MANIFEST_URL = "https://raw.githubusercontent.com/pranav520214/Privreach/master/version.json"


def get_git_commit_hash(repo_dir: str = ".") -> str:
    """Attempt to retrieve the short git commit hash if running in a git repo."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=2
        )
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return "release"


def get_version_info(repo_dir: str = ".") -> Dict[str, Any]:
    """Return comprehensive system version and build telemetry."""
    return {
        "version": VERSION,
        "channel": BUILD_CHANNEL,
        "release_date": RELEASE_DATE,
        "min_compatible": MIN_COMPATIBLE_VERSION,
        "git_commit": get_git_commit_hash(repo_dir),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "platform": sys.platform,
        "manifest_url": DEFAULT_OTA_MANIFEST_URL,
    }
