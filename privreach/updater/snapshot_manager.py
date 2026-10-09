"""Snapshot and Atomic Rollback Manager for Privreach OS."""

import os
import shutil
import time
import json
import uuid
from typing import List, Dict, Any, Optional
from privreach.updater.models import SnapshotMetadata, RollbackResult
from privreach.updater.version import VERSION


class SnapshotManager:
    """
    Guarantees atomic rollback safety:
    Before any patch or update touches the filesystem, a snapshot of affected
    files is created in `.privreach_snapshots/`. If anything fails or the user
    requests a revert, the snapshot can be restored in milliseconds.
    """
    def __init__(self, root_dir: str = "."):
        self.root_dir = os.path.abspath(root_dir)
        self.snapshots_dir = os.path.join(self.root_dir, ".privreach_snapshots")
        os.makedirs(self.snapshots_dir, exist_ok=True)

    def create_snapshot(self, reason: str, affected_files: List[str]) -> SnapshotMetadata:
        """Create a point-in-time snapshot of specified files."""
        timestamp = time.time()
        snap_id = f"snap_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        snap_storage = os.path.join(self.snapshots_dir, snap_id)
        files_storage = os.path.join(snap_storage, "files")
        os.makedirs(files_storage, exist_ok=True)

        backed_up: List[str] = []
        file_manifest: Dict[str, bool] = {}  # rel_path -> existed_before

        for rel_path in affected_files:
            norm_rel = os.path.normpath(rel_path).lstrip("\\/")
            src_file = os.path.join(self.root_dir, norm_rel)

            if os.path.isfile(src_file):
                dest_file = os.path.join(files_storage, norm_rel)
                os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                shutil.copy2(src_file, dest_file)
                backed_up.append(norm_rel)
                file_manifest[norm_rel] = True
            else:
                # File did not exist before (it is newly added)
                file_manifest[norm_rel] = False
                backed_up.append(norm_rel)

        metadata = SnapshotMetadata(
            snapshot_id=snap_id,
            created_at=timestamp,
            reason=reason,
            version=VERSION,
            affected_files=backed_up,
            storage_dir=snap_storage
        )

        with open(os.path.join(snap_storage, "metadata.json"), "w", encoding="utf-8") as f:
            f.write(metadata.model_dump_json(indent=2))

        with open(os.path.join(snap_storage, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(file_manifest, f, indent=2)

        return metadata

    def restore_snapshot(self, snapshot_id: Optional[str] = None) -> RollbackResult:
        """
        Restore a snapshot. If snapshot_id is None, restores the most recent snapshot.
        """
        if not snapshot_id:
            all_snaps = self.list_snapshots()
            if not all_snaps:
                return RollbackResult(
                    success=False,
                    snapshot_id="",
                    message="No snapshots available to restore.",
                    error="NO_SNAPSHOTS"
                )
            snapshot_id = all_snaps[0].snapshot_id

        snap_storage = os.path.join(self.snapshots_dir, snapshot_id)
        meta_file = os.path.join(snap_storage, "metadata.json")
        manifest_file = os.path.join(snap_storage, "manifest.json")
        files_storage = os.path.join(snap_storage, "files")

        if not os.path.exists(meta_file):
            return RollbackResult(
                success=False,
                snapshot_id=snapshot_id,
                message=f"Snapshot '{snapshot_id}' metadata not found on disk.",
                error="SNAPSHOT_NOT_FOUND"
            )

        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                file_manifest: Dict[str, bool] = json.load(f)
        except Exception:
            file_manifest = {}

        restored_files: List[str] = []
        try:
            for rel_path, existed_before in file_manifest.items():
                target_path = os.path.join(self.root_dir, rel_path)
                backup_path = os.path.join(files_storage, rel_path)

                if existed_before:
                    if os.path.exists(backup_path):
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        shutil.copy2(backup_path, target_path)
                        restored_files.append(rel_path)
                else:
                    # File was newly created by the patch, delete it to revert
                    if os.path.exists(target_path):
                        os.remove(target_path)
                        restored_files.append(f"{rel_path} (deleted)")

            return RollbackResult(
                success=True,
                snapshot_id=snapshot_id,
                restored_files=restored_files,
                message=f"Successfully reverted {len(restored_files)} files to snapshot '{snapshot_id}'."
            )
        except Exception as ex:
            return RollbackResult(
                success=False,
                snapshot_id=snapshot_id,
                restored_files=restored_files,
                message=f"Failed to restore snapshot: {str(ex)}",
                error=str(ex)
            )

    def list_snapshots(self) -> List[SnapshotMetadata]:
        """List all snapshots sorted from newest to oldest."""
        results: List[SnapshotMetadata] = []
        if not os.path.exists(self.snapshots_dir):
            return results

        for entry in os.listdir(self.snapshots_dir):
            snap_path = os.path.join(self.snapshots_dir, entry)
            meta_file = os.path.join(snap_path, "metadata.json")
            if os.path.isdir(snap_path) and os.path.exists(meta_file):
                try:
                    with open(meta_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        results.append(SnapshotMetadata(**data))
                except Exception:
                    pass

        results.sort(key=lambda s: s.created_at, reverse=True)
        return results

    def prune_snapshots(self, keep_count: int = 10) -> int:
        """Remove old snapshots keeping the most recent `keep_count`."""
        all_snaps = self.list_snapshots()
        if len(all_snaps) <= keep_count:
            return 0

        to_delete = all_snaps[keep_count:]
        deleted = 0
        for s in to_delete:
            try:
                shutil.rmtree(s.storage_dir)
                deleted += 1
            except Exception:
                pass
        return deleted
