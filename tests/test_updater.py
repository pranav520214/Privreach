"""Comprehensive Test Suite for Privreach OS Modern Patching & Updation System."""

import os
import shutil
import tempfile
import pytest

from privreach.updater.version import VERSION, get_version_info
from privreach.updater.models import (
    PatchManifest,
    PatchOperation,
    PatchOpType
)
from privreach.updater.snapshot_manager import SnapshotManager
from privreach.updater.patch_engine import PatchEngine, calculate_sha256
from privreach.updater.patch_builder import PatchBuilder
from privreach.updater.ota_client import parse_semver, OTAClient


@pytest.fixture
def temp_workspace():
    tmp_dir = tempfile.mkdtemp(prefix="privreach_test_")
    # Create sample files
    f1 = os.path.join(tmp_dir, "config.py")
    with open(f1, "w", encoding="utf-8") as f:
        f.write("# Original Config v1\nDEBUG = True\n")

    f2 = os.path.join(tmp_dir, "lib", "util.py")
    os.makedirs(os.path.dirname(f2), exist_ok=True)
    with open(f2, "w", encoding="utf-8") as f:
        f.write("def helper(): return 'original'\n")

    yield tmp_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)


def test_version_metadata():
    info = get_version_info()
    assert info["version"] == VERSION
    assert info["version"] == "2.0.0"
    assert info["channel"] == "stable"
    assert "git_commit" in info


def test_semver_parsing():
    assert parse_semver("v2.1.0") == (2, 1, 0)
    assert parse_semver("2.0.1") == (2, 0, 1)
    assert parse_semver("v2.1.0") > parse_semver("v2.0.0")
    assert parse_semver("v1.9.9") < parse_semver("v2.0.0")


def test_snapshot_lifecycle(temp_workspace):
    manager = SnapshotManager(root_dir=temp_workspace)
    f1_rel = "config.py"
    f1_path = os.path.join(temp_workspace, f1_rel)

    # 1. Create Snapshot
    snap = manager.create_snapshot("test_backup", [f1_rel])
    assert snap.snapshot_id.startswith("snap_")
    assert f1_rel in snap.affected_files

    # 2. Modify original file
    with open(f1_path, "w", encoding="utf-8") as f:
        f.write("# Corrupted Config\nDEBUG = False\n")

    # 3. Restore Snapshot
    res = manager.restore_snapshot(snap.snapshot_id)
    assert res.success is True

    # 4. Verify Content Reverted
    with open(f1_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Original Config v1" in content


def test_patch_application_and_verification(temp_workspace):
    builder = PatchBuilder(root_dir=temp_workspace)
    engine = PatchEngine(root_dir=temp_workspace)

    f1_rel = "config.py"
    f1_path = os.path.join(temp_workspace, f1_rel)

    # Prepare updated file content
    with open(f1_path, "w", encoding="utf-8") as f:
        f.write("# Patched Config v2\nDEBUG = False\nOPTIMIZE = True\n")

    # Build patch
    manifest = builder.build_patch(
        patch_id="patch-001",
        title="Optimization Patch",
        description="Updates config",
        target_version="2.0.1",
        file_paths=[f1_rel]
    )

    # Revert config to original before applying patch
    with open(f1_path, "w", encoding="utf-8") as f:
        f.write("# Original Config v1\nDEBUG = True\n")

    # Apply Patch
    res = engine.apply_manifest(manifest, auto_rollback=True)
    assert res.success is True
    assert res.operations_applied == 1

    # Verify patched content
    with open(f1_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Patched Config v2" in content
    assert "OPTIMIZE = True" in content


def test_pre_condition_validation_rejection(temp_workspace):
    engine = PatchEngine(root_dir=temp_workspace)

    manifest = PatchManifest(
        patch_id="bad-patch",
        title="Bad Pre-Hash",
        operations=[
            PatchOperation(
                op_type=PatchOpType.FILE_REPLACE,
                path="config.py",
                content_b64="bmV3IGNvbnRlbnQ=",
                pre_sha256="0000000000000000000000000000000000000000000000000000000000000000"  # Invalid hash
            )
        ]
    )

    res = engine.apply_manifest(manifest, auto_rollback=True)
    assert res.success is False
    assert "Pre-patch validation failed" in res.message

    # File should remain unmodified
    with open(os.path.join(temp_workspace, "config.py"), "r", encoding="utf-8") as f:
        content = f.read()
    assert "Original Config v1" in content


def test_automatic_rollback_on_post_hash_mismatch(temp_workspace):
    engine = PatchEngine(root_dir=temp_workspace)
    f1_path = os.path.join(temp_workspace, "config.py")

    manifest = PatchManifest(
        patch_id="fail-post-patch",
        title="Mismatch Post-Hash",
        operations=[
            PatchOperation(
                op_type=PatchOpType.FILE_REPLACE,
                path="config.py",
                content_b64="bmV3IGNvbnRlbnQ=",
                post_sha256="ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"  # Will fail verification
            )
        ]
    )

    res = engine.apply_manifest(manifest, auto_rollback=True)
    assert res.success is False
    assert "Automatically rolled back" in res.message

    # Content must still be original
    with open(f1_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Original Config v1" in content
