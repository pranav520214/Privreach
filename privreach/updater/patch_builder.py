"""Developer and Release Engineering Tooling: Generate and Sign .privpatch bundles."""

import os
import sys
import gzip
import json
import base64
import time
import uuid
import difflib
from typing import List, Dict, Any, Optional

from privreach.updater.models import (
    PatchManifest,
    PatchOperation,
    PatchOpType
)
from privreach.updater.patch_engine import calculate_sha256
from privreach.updater.version import VERSION


class PatchBuilder:
    """
    Constructs cryptographically verified `.privpatch` bundles from file lists
    or directory comparisons.
    """
    def __init__(self, root_dir: str = "."):
        self.root_dir = os.path.abspath(root_dir)

    def create_file_replacement_op(
        self,
        rel_path: str,
        pre_file_path: Optional[str] = None,
        pre_sha256: Optional[str] = None
    ) -> PatchOperation:
        """Create a FILE_REPLACE operation with pre/post sha256 checksums."""
        full_path = os.path.join(self.root_dir, rel_path)
        with open(full_path, "rb") as f:
            raw_bytes = f.read()

        b64_content = base64.b64encode(raw_bytes).decode("ascii")
        post_sha = calculate_sha256(full_path)

        pre_sha = pre_sha256
        if pre_sha is None and pre_file_path and os.path.isfile(pre_file_path):
            pre_sha = calculate_sha256(pre_file_path)

        return PatchOperation(
            op_type=PatchOpType.FILE_REPLACE,
            path=rel_path.replace("\\", "/"),
            content_b64=b64_content,
            pre_sha256=pre_sha,
            post_sha256=post_sha,
            is_binary=False
        )

    def create_diff_patch_op(self, rel_path: str, old_content: str, new_content: str) -> PatchOperation:
        """Create a unified diff FILE_PATCH operation."""
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        diff = list(difflib.unified_diff(old_lines, new_lines, fromfile=f"a/{rel_path}", tofile=f"b/{rel_path}"))
        diff_text = "".join(diff)

        # Pre/post hashes
        pre_sha = None
        current_path = os.path.join(self.root_dir, rel_path)
        if os.path.exists(current_path):
            pre_sha = calculate_sha256(current_path)

        import hashlib
        post_sha = hashlib.sha256(new_content.encode("utf-8")).hexdigest()

        return PatchOperation(
            op_type=PatchOpType.FILE_PATCH,
            path=rel_path.replace("\\", "/"),
            diff_text=diff_text,
            pre_sha256=pre_sha,
            post_sha256=post_sha
        )

    def build_patch(
        self,
        patch_id: str,
        title: str,
        description: str,
        target_version: str,
        source_version: str = VERSION,
        file_paths: Optional[List[str]] = None,
        operations: Optional[List[PatchOperation]] = None
    ) -> PatchManifest:
        """Assemble a complete PatchManifest."""
        ops = list(operations or [])
        if file_paths:
            for p in file_paths:
                ops.append(self.create_file_replacement_op(p))

        return PatchManifest(
            patch_id=patch_id,
            title=title,
            description=description,
            source_version=source_version,
            target_version=target_version,
            created_at=time.time(),
            operations=ops,
            supports_hot_reload=True
        )

    def export_patch_bundle(self, manifest: PatchManifest, output_path: str, compress: bool = True) -> str:
        """Export manifest to a .privpatch (gzip) or .json file."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        raw_json = manifest.model_dump_json(indent=2)

        if compress or output_path.endswith(".privpatch") or output_path.endswith(".gz"):
            with gzip.open(output_path, "wt", encoding="utf-8") as f:
                f.write(raw_json)
        else:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(raw_json)

        return os.path.abspath(output_path)
