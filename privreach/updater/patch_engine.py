"""Patch Engine for Privreach OS: Atomic differential patching, verification, and live hot-reloading."""

import os
import sys
import gzip
import json
import base64
import hashlib
import difflib
import importlib
import time
from typing import List, Dict, Any, Optional, Tuple

from privreach.updater.models import (
    PatchManifest,
    PatchOperation,
    PatchOpType,
    PatchResult,
    RollbackResult
)
from privreach.updater.snapshot_manager import SnapshotManager
from privreach.updater.version import VERSION


def calculate_sha256(file_path: str) -> Optional[str]:
    """Compute SHA256 checksum of file if it exists, otherwise None."""
    if not os.path.isfile(file_path):
        return None
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def apply_unified_diff(original_text: str, diff_text: str) -> str:
    """Apply a unified diff patch to source text."""
    # Split into lines preserving endings
    orig_lines = original_text.splitlines(keepends=True)
    patch_lines = diff_text.splitlines(keepends=True)

    # Use difflib or simple line patcher
    # We parse standard diff headers and hunk markers @@ -l,s +l,s @@
    result_lines: List[str] = []
    i = 0
    in_hunk = False

    orig_idx = 0
    for line in patch_lines:
        if line.startswith("---") or line.startswith("+++"):
            continue
        if line.startswith("@@"):
            # Parse hunk header
            in_hunk = True
            parts = line.split("@@")
            if len(parts) >= 3:
                header = parts[1].strip()
                # format: -start,count +start,count
                # e.g., -1,3 +1,3
                try:
                    src_part = header.split(" ")[0].lstrip("-")
                    src_start = int(src_part.split(",")[0]) - 1
                    while orig_idx < src_start and orig_idx < len(orig_lines):
                        result_lines.append(orig_lines[orig_idx])
                        orig_idx += 1
                except Exception:
                    pass
            continue

        if not in_hunk:
            continue

        if line.startswith("+"):
            result_lines.append(line[1:])
        elif line.startswith("-"):
            orig_idx += 1
        elif line.startswith(" ") or line.startswith("\t"):
            if orig_idx < len(orig_lines):
                result_lines.append(orig_lines[orig_idx])
                orig_idx += 1
            else:
                result_lines.append(line[1:])

    while orig_idx < len(orig_lines):
        result_lines.append(orig_lines[orig_idx])
        orig_idx += 1

    return "".join(result_lines)


class PatchEngine:
    """
    High-Performance Zero-Downtime Patching Engine.
    Executes pre-validation, atomic file patching, snapshot protection,
    hot-reloading of Python modules, and automatic rollback on errors.
    """
    def __init__(self, root_dir: str = "."):
        self.root_dir = os.path.abspath(root_dir)
        self.snapshot_manager = SnapshotManager(root_dir=self.root_dir)
        self.history_file = os.path.join(self.root_dir, ".privreach_snapshots", "patch_history.jsonl")

    def validate_pre_conditions(self, manifest: PatchManifest) -> Tuple[bool, List[str]]:
        """
        Validate all expected pre-hashes against files currently on disk.
        Returns (is_valid, list_of_error_messages).
        """
        errors: List[str] = []
        for op in manifest.operations:
            target_path = os.path.join(self.root_dir, os.path.normpath(op.path).lstrip("\\/"))

            if op.pre_sha256 is not None:
                if not os.path.exists(target_path):
                    errors.append(f"Target file '{op.path}' does not exist on disk, but pre_sha256 was expected.")
                else:
                    actual_hash = calculate_sha256(target_path)
                    if actual_hash != op.pre_sha256:
                        errors.append(
                            f"Checksum mismatch for '{op.path}': Expected {op.pre_sha256[:10]}..., got {actual_hash[:10]}..."
                        )

            if op.op_type == PatchOpType.FILE_PATCH and not os.path.exists(target_path):
                errors.append(f"Cannot apply diff patch to '{op.path}': File does not exist.")

        return len(errors) == 0, errors

    def apply_manifest(self, manifest: PatchManifest, auto_rollback: bool = True) -> PatchResult:
        """
        Execute an atomic patch application with snapshot protection and validation.
        """
        # 1. Pre-condition validation
        is_valid, errors = self.validate_pre_conditions(manifest)
        if not is_valid:
            return PatchResult(
                success=False,
                patch_id=manifest.patch_id,
                target_version=manifest.target_version,
                message=f"Pre-patch validation failed with {len(errors)} errors.",
                error="; ".join(errors)
            )

        # 2. Collect affected files and create snapshot
        affected_files = [op.path for op in manifest.operations if op.op_type != PatchOpType.HOT_RELOAD]
        snapshot = self.snapshot_manager.create_snapshot(
            reason=f"pre-patch:{manifest.patch_id}",
            affected_files=affected_files
        )

        modified_files: List[str] = []
        hot_reloaded: List[str] = []
        ops_applied = 0

        try:
            for op in manifest.operations:
                norm_rel = os.path.normpath(op.path).lstrip("\\/")
                target_path = os.path.join(self.root_dir, norm_rel)

                if op.op_type == PatchOpType.FILE_REPLACE:
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    if op.content_b64 is not None:
                        content_bytes = base64.b64decode(op.content_b64)
                    else:
                        content_bytes = b""

                    tmp_path = f"{target_path}.tmp_{time.time_ns()}"
                    with open(tmp_path, "wb") as f:
                        f.write(content_bytes)

                    # Verify post-hash on temp file before replacing
                    if op.post_sha256:
                        actual_post = calculate_sha256(tmp_path)
                        if actual_post != op.post_sha256:
                            os.remove(tmp_path)
                            raise ValueError(f"Post-hash verification failed for '{op.path}': expected {op.post_sha256}, got {actual_post}")

                    # Atomic replace
                    if os.path.exists(target_path):
                        os.replace(tmp_path, target_path)
                    else:
                        os.rename(tmp_path, target_path)

                    modified_files.append(norm_rel)
                    ops_applied += 1

                elif op.op_type == PatchOpType.FILE_PATCH:
                    with open(target_path, "r", encoding="utf-8") as f:
                        orig_text = f.read()

                    patched_text = apply_unified_diff(orig_text, op.diff_text or "")
                    tmp_path = f"{target_path}.tmp_{time.time_ns()}"
                    with open(tmp_path, "w", encoding="utf-8") as f:
                        f.write(patched_text)

                    if op.post_sha256:
                        actual_post = calculate_sha256(tmp_path)
                        if actual_post != op.post_sha256:
                            os.remove(tmp_path)
                            raise ValueError(f"Post-patch hash mismatch for '{op.path}': expected {op.post_sha256}, got {actual_post}")

                    os.replace(tmp_path, target_path)
                    modified_files.append(norm_rel)
                    ops_applied += 1

                elif op.op_type == PatchOpType.FILE_DELETE:
                    if os.path.exists(target_path):
                        os.remove(target_path)
                        modified_files.append(f"{norm_rel} (deleted)")
                    ops_applied += 1

                elif op.op_type == PatchOpType.HOT_RELOAD:
                    mod_name = op.module_name or op.path.replace("/", ".").replace("\\", ".").rstrip(".py")
                    if mod_name in sys.modules:
                        try:
                            importlib.reload(sys.modules[mod_name])
                            hot_reloaded.append(mod_name)
                        except Exception as e:
                            print(f"[WARN] Hot-reload failed for {mod_name}: {e}")
                    ops_applied += 1

            # Auto-reload modified python files if hot-reload is supported
            if manifest.supports_hot_reload:
                for fpath in modified_files:
                    if fpath.endswith(".py"):
                        mod_name = fpath.replace("/", ".").replace("\\", ".").rstrip(".py")
                        if mod_name in sys.modules and mod_name not in hot_reloaded:
                            try:
                                importlib.reload(sys.modules[mod_name])
                                hot_reloaded.append(mod_name)
                            except Exception:
                                pass

            # 3. Log patch history
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            with open(self.history_file, "a", encoding="utf-8") as f:
                record = {
                    "patch_id": manifest.patch_id,
                    "target_version": manifest.target_version,
                    "applied_at": time.time(),
                    "snapshot_id": snapshot.snapshot_id,
                    "files_modified": modified_files,
                    "hot_reloaded": hot_reloaded
                }
                f.write(json.dumps(record) + "\n")

            return PatchResult(
                success=True,
                patch_id=manifest.patch_id,
                target_version=manifest.target_version,
                operations_applied=ops_applied,
                files_modified=modified_files,
                hot_reloaded_modules=hot_reloaded,
                snapshot_id=snapshot.snapshot_id,
                message=f"Successfully applied patch '{manifest.patch_id}' ({ops_applied} operations)."
            )

        except Exception as ex:
            # Automatic Rollback
            if auto_rollback:
                rb_res = self.snapshot_manager.restore_snapshot(snapshot.snapshot_id)
                msg = f"Patch failed: {str(ex)}. Automatically rolled back to snapshot '{snapshot.snapshot_id}' ({len(rb_res.restored_files)} files restored)."
            else:
                msg = f"Patch failed: {str(ex)}."

            return PatchResult(
                success=False,
                patch_id=manifest.patch_id,
                target_version=manifest.target_version,
                operations_applied=ops_applied,
                files_modified=modified_files,
                snapshot_id=snapshot.snapshot_id,
                message=msg,
                error=str(ex)
            )

    def apply_patch_file(self, patch_path: str, auto_rollback: bool = True) -> PatchResult:
        """
        Load and apply a `.privpatch` or gzip-compressed patch bundle from file.
        """
        if not os.path.exists(patch_path):
            return PatchResult(
                success=False,
                patch_id="",
                target_version="",
                message=f"Patch file '{patch_path}' not found.",
                error="FILE_NOT_FOUND"
            )

        try:
            # Try reading as gzip
            try:
                with gzip.open(patch_path, "rt", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                with open(patch_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

            manifest = PatchManifest(**data)
            return self.apply_manifest(manifest, auto_rollback=auto_rollback)
        except Exception as ex:
            return PatchResult(
                success=False,
                patch_id="",
                target_version="",
                message=f"Failed to parse patch bundle: {str(ex)}",
                error=str(ex)
            )
