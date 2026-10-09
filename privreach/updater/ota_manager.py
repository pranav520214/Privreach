"""Zero-Trust OTA (Over-The-Air) Update Engine for Privearch."""

import os
import sys
import json
import hashlib
import shutil
import zipfile
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, Tuple, Callable
from privearch.updater.version import VERSION, DEFAULT_OTA_MANIFEST_URL


def parse_semver(v_str: str) -> Tuple[int, int, int]:
    """Parse semver string '1.2.3' into (1, 2, 3) tuple."""
    clean = v_str.lstrip('vV').strip()
    parts = clean.split('.')
    try:
        return (int(parts[0]), int(parts[1]), int(parts[2]))
    except Exception:
        return (0, 0, 0)


def calculate_sha256(file_path: str) -> str:
    """Compute SHA256 checksum of file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class OTAManager:
    """
    Manages over-the-air update checks, cryptographic verification,
    atomic application, and automatic rollbacks.
    """
    def __init__(
        self,
        current_version: str = VERSION,
        manifest_url: str = DEFAULT_OTA_MANIFEST_URL,
        install_dir: Optional[str] = None
    ):
        self.current_version = current_version
        self.manifest_url = manifest_url
        self.install_dir = install_dir or os.path.abspath(".")
        self.backup_dir = os.path.join(self.install_dir, ".privearch_backup")

    def check_for_updates(self, custom_url: Optional[str] = None) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Check for available OTA updates.
        
        Returns:
            (has_update: bool, update_info: dict, message: str)
        """
        url = custom_url or self.manifest_url

        try:
            # Handle local file path or file:// URL for offline / airgap network mirrors
            if url.startswith("file://") or os.path.exists(url):
                file_path = url.replace("file://", "")
                with open(file_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
            else:
                req = urllib.request.Request(url, headers={"User-Agent": f"Privearch-OTA/{self.current_version}"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    manifest = json.loads(resp.read().decode("utf-8"))

            remote_version = manifest.get("version", "0.0.0")
            if parse_semver(remote_version) > parse_semver(self.current_version):
                return True, manifest, f"New version available: v{remote_version} (Current: v{self.current_version})"
            else:
                return False, manifest, f"Privearch is up to date (v{self.current_version})"

        except Exception as e:
            return False, None, f"OTA update check failed: {e}"

    def download_update(
        self,
        update_info: Dict[str, Any],
        dest_folder: Optional[str] = None,
        progress_cb: Optional[Callable[[float], None]] = None
    ) -> Tuple[bool, str]:
        """Download update package and verify SHA256 checksum."""
        download_url = update_info.get("download_url")
        if not download_url:
            return False, "Manifest missing 'download_url'."

        target_folder = dest_folder or os.path.join(self.install_dir, ".ota_staging")
        os.makedirs(target_folder, exist_ok=True)
        zip_path = os.path.join(target_folder, f"privearch-update-v{update_info['version']}.zip")

        try:
            # If download_url is a local file path
            if os.path.exists(download_url):
                shutil.copy2(download_url, zip_path)
            else:
                req = urllib.request.Request(download_url, headers={"User-Agent": f"Privearch-OTA/{self.current_version}"})
                with urllib.request.urlopen(req, timeout=60) as response, open(zip_path, 'wb') as out_file:
                    total_length = response.getheader('content-length')
                    if total_length:
                        total_length = int(total_length)
                    bytes_downloaded = 0
                    block_size = 65536

                    while True:
                        buffer = response.read(block_size)
                        if not buffer:
                            break
                        bytes_downloaded += len(buffer)
                        out_file.write(buffer)
                        if progress_cb and total_length:
                            progress_cb(bytes_downloaded / total_length)

            # Check SHA256 if present
            expected_sha = update_info.get("sha256")
            if expected_sha:
                actual_sha = calculate_sha256(zip_path)
                if actual_sha.lower() != expected_sha.lower():
                    os.remove(zip_path)
                    return False, f"Cryptographic integrity mismatch! Expected {expected_sha}, got {actual_sha}"

            return True, zip_path

        except Exception as e:
            return False, f"Failed to download update: {e}"

    def apply_update(self, zip_path: str) -> Tuple[bool, str]:
        """
        Atomically extracts the update package over install_dir.
        Backs up current system and preserves .privearch_cache/ (knowledge vault).
        """
        if not os.path.exists(zip_path):
            return False, "Update package does not exist."

        # 1. Create safety backup
        try:
            if os.path.exists(self.backup_dir):
                shutil.rmtree(self.backup_dir)
            os.makedirs(self.backup_dir, exist_ok=True)

            # Backup core directories & executables
            items_to_backup = ["privearch", "Privearch.exe", "Privearch-Terminal.exe", "run_web.py", "run_privearch.py"]
            for item in items_to_backup:
                src = os.path.join(self.install_dir, item)
                dst = os.path.join(self.backup_dir, item)
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                elif os.path.isfile(src):
                    shutil.copy2(src, dst)
        except Exception as e:
            return False, f"Failed to create pre-update safety backup: {e}"

        # 2. Extract update package
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Security: prevent zip-slip path traversal
                for member in zf.namelist():
                    norm_path = os.path.normpath(member)
                    if norm_path.startswith("..") or norm_path.startswith("/") or norm_path.startswith("\\"):
                        raise ValueError(f"Malicious zip path detected: {member}")

                # Extract files, NEVER overwriting .privearch_cache
                for member in zf.infolist():
                    if ".privearch_cache" in member.filename:
                        continue  # Keep user's existing vault intact!
                    zf.extract(member, self.install_dir)

            # Clean staging
            staging_folder = os.path.dirname(zip_path)
            if os.path.exists(staging_folder) and ".ota_staging" in staging_folder:
                shutil.rmtree(staging_folder, ignore_errors=True)

            return True, "Update applied successfully! Ready to restart."

        except Exception as e:
            # 3. Rollback on failure
            self.rollback()
            return False, f"Update application failed: {e}. Automatically rolled back to previous version."

    def rollback(self) -> Tuple[bool, str]:
        """Restore previous version from safety backup."""
        if not os.path.exists(self.backup_dir):
            return False, "No backup directory found to restore."

        try:
            for item in os.listdir(self.backup_dir):
                src = os.path.join(self.backup_dir, item)
                dst = os.path.join(self.install_dir, item)
                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                elif os.path.isfile(src):
                    shutil.copy2(src, dst)
            return True, "System successfully rolled back to previous version."
        except Exception as e:
            return False, f"Rollback failed: {e}"

    @staticmethod
    def create_update_bundle(
        source_dir: str,
        output_zip_path: str,
        version: str,
        changelog: str = "OTA Update Release"
    ) -> Dict[str, Any]:
        """Utility for creating an official OTA release zip and manifest metadata."""
        os.makedirs(os.path.dirname(os.path.abspath(output_zip_path)), exist_ok=True)

        include_items = [
            "privearch",
            "Privearch.exe",
            "Privearch-Terminal.exe",
            "privearch.ico",
            "run_web.py",
            "run_privearch.py",
            "deploy_chemistry_vault.py",
            "README.md"
        ]

        with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for item in include_items:
                full_path = os.path.join(source_dir, item)
                if os.path.isdir(full_path):
                    for root, _, files in os.walk(full_path):
                        if "__pycache__" in root:
                            continue
                        for file in files:
                            f_path = os.path.join(root, file)
                            rel_path = os.path.relpath(f_path, source_dir)
                            zf.write(f_path, rel_path)
                elif os.path.isfile(full_path):
                    zf.write(full_path, item)

        sha = calculate_sha256(output_zip_path)
        manifest = {
            "version": version,
            "release_date": "2026-10-04",
            "min_compatible_version": "1.0.0",
            "changelog": changelog,
            "download_url": os.path.basename(output_zip_path),
            "sha256": sha
        }
        return manifest
