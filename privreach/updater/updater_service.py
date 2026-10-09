"""Unified Updater Service for Privreach OS."""

import os
import time
from typing import Dict, Any, List, Optional

from privreach.updater.models import (
    UpdateCheckResult,
    PatchResult,
    RollbackResult,
    SnapshotMetadata,
    PatchManifest
)
from privreach.updater.version import VERSION, get_version_info, DEFAULT_OTA_MANIFEST_URL
from privreach.updater.snapshot_manager import SnapshotManager
from privreach.updater.patch_engine import PatchEngine
from privreach.updater.ota_client import OTAClient


class UpdaterService:
    """
    Central orchestration service managing update telemetry,
    patch applications, snapshots, and rollbacks for REST APIs and UIs.
    """
    def __init__(self, root_dir: str = "."):
        self.root_dir = os.path.abspath(root_dir)
        self.snapshot_manager = SnapshotManager(root_dir=self.root_dir)
        self.patch_engine = PatchEngine(root_dir=self.root_dir)
        self.ota_client = OTAClient(root_dir=self.root_dir)

    def get_status(self) -> Dict[str, Any]:
        """Return comprehensive updater status and snapshot history."""
        info = get_version_info(self.root_dir)
        snapshots = self.snapshot_manager.list_snapshots()
        latest_snap = snapshots[0].snapshot_id if snapshots else None

        return {
            **info,
            "total_snapshots": len(snapshots),
            "latest_snapshot": latest_snap,
            "snapshots": [s.model_dump() for s in snapshots[:5]],
            "can_rollback": len(snapshots) > 0
        }

    def check_for_updates(self, custom_url: Optional[str] = None) -> UpdateCheckResult:
        """Check for updates."""
        return self.ota_client.check_for_updates(custom_url=custom_url)

    def apply_patch_file(self, file_path: str, auto_rollback: bool = True) -> PatchResult:
        """Apply a local patch file."""
        return self.patch_engine.apply_patch_file(file_path, auto_rollback=auto_rollback)

    def apply_patch_manifest(self, manifest: PatchManifest, auto_rollback: bool = True) -> PatchResult:
        """Apply a patch manifest object."""
        return self.patch_engine.apply_manifest(manifest, auto_rollback=auto_rollback)

    def rollback_to_snapshot(self, snapshot_id: Optional[str] = None) -> RollbackResult:
        """Rollback to a specified snapshot, or the latest snapshot."""
        return self.snapshot_manager.restore_snapshot(snapshot_id=snapshot_id)

    def create_snapshot(self, reason: str = "manual_backup", files: Optional[List[str]] = None) -> SnapshotMetadata:
        """Create a manual snapshot."""
        if not files:
            # Default to core privreach code files
            files = []
            for root, _, filenames in os.walk(os.path.join(self.root_dir, "privreach")):
                for fn in filenames:
                    files.append(os.path.relpath(os.path.join(root, fn), self.root_dir))

        return self.snapshot_manager.create_snapshot(reason=reason, affected_files=files)

    def list_snapshots(self) -> List[SnapshotMetadata]:
        return self.snapshot_manager.list_snapshots()


# Singleton instance
_service: Optional[UpdaterService] = None

def get_updater_service(root_dir: str = ".") -> UpdaterService:
    global _service
    if _service is None or _service.root_dir != os.path.abspath(root_dir):
        _service = UpdaterService(root_dir=root_dir)
    return _service
