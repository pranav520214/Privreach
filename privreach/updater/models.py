"""Data schemas and Pydantic models for the Privreach Modern Patching & Updation System."""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class PatchOpType(str, Enum):
    FILE_REPLACE = "FILE_REPLACE"
    FILE_PATCH = "FILE_PATCH"
    FILE_DELETE = "FILE_DELETE"
    HOT_RELOAD = "HOT_RELOAD"
    RUN_COMMAND = "RUN_COMMAND"


class PatchOperation(BaseModel):
    op_type: PatchOpType
    path: str
    content_b64: Optional[str] = None
    diff_text: Optional[str] = None
    pre_sha256: Optional[str] = None
    post_sha256: Optional[str] = None
    is_binary: bool = False
    module_name: Optional[str] = None


class PatchManifest(BaseModel):
    patch_id: str
    title: str
    description: str = ""
    source_version: str = "2.0.0"
    target_version: str = "2.0.1"
    channel: str = "stable"
    created_at: float = 0.0
    author: str = "Privreach Architecture"
    operations: List[PatchOperation] = Field(default_factory=list)
    requires_restart: bool = False
    supports_hot_reload: bool = True
    signature: Optional[str] = None


class SnapshotMetadata(BaseModel):
    snapshot_id: str
    created_at: float
    reason: str
    version: str
    affected_files: List[str] = Field(default_factory=list)
    storage_dir: str


class UpdateCheckResult(BaseModel):
    has_update: bool
    current_version: str
    latest_version: str
    channel: str
    release_date: Optional[str] = None
    changelog: Optional[str] = None
    download_url: Optional[str] = None
    sha256: Optional[str] = None
    is_patch: bool = False
    patch_id: Optional[str] = None
    message: str = ""


class PatchResult(BaseModel):
    success: bool
    patch_id: str
    target_version: str
    operations_applied: int = 0
    files_modified: List[str] = Field(default_factory=list)
    hot_reloaded_modules: List[str] = Field(default_factory=list)
    snapshot_id: Optional[str] = None
    message: str = ""
    error: Optional[str] = None


class RollbackResult(BaseModel):
    success: bool
    snapshot_id: str
    restored_files: List[str] = Field(default_factory=list)
    message: str = ""
    error: Optional[str] = None
