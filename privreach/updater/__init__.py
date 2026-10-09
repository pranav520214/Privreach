"""Privreach OS Modern Patching & Updation Subsystem."""

from privreach.updater.version import (
    VERSION,
    BUILD_CHANNEL,
    RELEASE_DATE,
    MIN_COMPATIBLE_VERSION,
    DEFAULT_OTA_MANIFEST_URL,
    get_version_info,
)
from privreach.updater.models import (
    PatchOpType,
    PatchOperation,
    PatchManifest,
    SnapshotMetadata,
    UpdateCheckResult,
    PatchResult,
    RollbackResult,
)
from privreach.updater.snapshot_manager import SnapshotManager
from privreach.updater.patch_engine import PatchEngine, calculate_sha256
from privreach.updater.patch_builder import PatchBuilder
from privreach.updater.ota_client import OTAClient
from privreach.updater.updater_service import UpdaterService, get_updater_service

__all__ = [
    "VERSION",
    "BUILD_CHANNEL",
    "RELEASE_DATE",
    "MIN_COMPATIBLE_VERSION",
    "DEFAULT_OTA_MANIFEST_URL",
    "get_version_info",
    "PatchOpType",
    "PatchOperation",
    "PatchManifest",
    "SnapshotMetadata",
    "UpdateCheckResult",
    "PatchResult",
    "RollbackResult",
    "SnapshotManager",
    "PatchEngine",
    "PatchBuilder",
    "OTAClient",
    "UpdaterService",
    "get_updater_service",
    "calculate_sha256",
]
