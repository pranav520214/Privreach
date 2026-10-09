"""OTA (Over-The-Air) Client for Privreach OS: Remote/offline update checker and downloader."""

import os
import json
import urllib.request
import urllib.error
import zipfile
import shutil
from typing import Optional, Callable, Tuple, Dict, Any

from privreach.updater.models import UpdateCheckResult, PatchResult
from privreach.updater.version import VERSION, DEFAULT_OTA_MANIFEST_URL
from privreach.updater.patch_engine import PatchEngine, calculate_sha256
from privreach.updater.snapshot_manager import SnapshotManager


def parse_semver(v_str: str) -> Tuple[int, int, int]:
    """Parse semver string into comparable tuple."""
    clean = v_str.lstrip("vV").strip()
    parts = clean.split(".")
    try:
        return (int(parts[0]), int(parts[1]), int(parts[2]))
    except Exception:
        return (0, 0, 0)


class OTAClient:
    """
    Communicates with release channels (or offline local airgap manifests),
    downloads signed bundles, validates SHA256 checksums, and coordinates
    installation through the PatchEngine.
    """
    def __init__(self, root_dir: str = ".", manifest_url: str = DEFAULT_OTA_MANIFEST_URL):
        self.root_dir = os.path.abspath(root_dir)
        self.manifest_url = manifest_url
        self.patch_engine = PatchEngine(root_dir=self.root_dir)
        self.snapshot_manager = SnapshotManager(root_dir=self.root_dir)

    def check_for_updates(self, custom_url: Optional[str] = None) -> UpdateCheckResult:
        """Query manifest URL or local path for new version availability."""
        url = custom_url or self.manifest_url

        try:
            if url.startswith("file://") or os.path.isfile(url):
                file_path = url.replace("file://", "")
                with open(file_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
            else:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": f"PrivreachOS-OTA/{VERSION}"}
                )
                with urllib.request.urlopen(req, timeout=6) as resp:
                    manifest = json.loads(resp.read().decode("utf-8"))

            remote_ver = manifest.get("version", "0.0.0")
            has_update = parse_semver(remote_ver) > parse_semver(VERSION)

            return UpdateCheckResult(
                has_update=has_update,
                current_version=VERSION,
                latest_version=remote_ver,
                channel=manifest.get("channel", "stable"),
                release_date=manifest.get("release_date"),
                changelog=manifest.get("changelog", ""),
                download_url=manifest.get("download_url"),
                sha256=manifest.get("sha256"),
                is_patch=manifest.get("is_patch", False),
                patch_id=manifest.get("patch_id"),
                message=f"New version v{remote_ver} available!" if has_update else f"Privreach OS is up to date (v{VERSION})."
            )

        except Exception as ex:
            return UpdateCheckResult(
                has_update=False,
                current_version=VERSION,
                latest_version=VERSION,
                channel="unknown",
                message=f"Update check failed: {str(ex)}"
            )

    def download_update(
        self,
        download_url: str,
        dest_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """Download remote update payload to local file with progress tracking."""
        os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)

        try:
            if download_url.startswith("file://") or os.path.isfile(download_url):
                src = download_url.replace("file://", "")
                shutil.copy2(src, dest_path)
                return True

            req = urllib.request.Request(
                download_url,
                headers={"User-Agent": f"PrivreachOS-OTA/{VERSION}"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                total_size = int(resp.headers.get("content-length", 0))
                downloaded = 0
                chunk_size = 65536

                with open(dest_path, "wb") as out_file:
                    while True:
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        out_file.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(downloaded, total_size)

            return True
        except Exception:
            return False

    def apply_update_package(self, package_path: str, expected_sha256: Optional[str] = None) -> PatchResult:
        """
        Verify integrity and apply an update package (supports .privpatch or .zip full release).
        """
        if not os.path.exists(package_path):
            return PatchResult(
                success=False,
                patch_id="",
                target_version="",
                message=f"Package not found: {package_path}",
                error="FILE_NOT_FOUND"
            )

        # Integrity Check
        if expected_sha256:
            actual_sha = calculate_sha256(package_path)
            if actual_sha != expected_sha256:
                return PatchResult(
                    success=False,
                    patch_id="",
                    target_version="",
                    message=f"SHA256 Checksum mismatch! Expected {expected_sha256}, got {actual_sha}",
                    error="CHECKSUM_MISMATCH"
                )

        # 1. Delta patch format
        if package_path.endswith(".privpatch"):
            return self.patch_engine.apply_patch_file(package_path)

        # 2. Full release zip
        if package_path.endswith(".zip"):
            # Create full snapshot before extracting
            snapshot = self.snapshot_manager.create_snapshot(
                reason=f"full_upgrade_{os.path.basename(package_path)}",
                affected_files=[]
            )
            try:
                with zipfile.ZipFile(package_path, "r") as zf:
                    zf.extractall(self.root_dir)

                return PatchResult(
                    success=True,
                    patch_id=os.path.basename(package_path),
                    target_version="latest",
                    message="Full release archive extracted successfully.",
                    snapshot_id=snapshot.snapshot_id
                )
            except Exception as e:
                self.snapshot_manager.restore_snapshot(snapshot.snapshot_id)
                return PatchResult(
                    success=False,
                    patch_id=os.path.basename(package_path),
                    target_version="",
                    message=f"Zip extraction failed: {e}. Rolled back.",
                    error=str(e)
                )

        return self.patch_engine.apply_patch_file(package_path)
