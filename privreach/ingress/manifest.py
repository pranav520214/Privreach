"""
Cryptographically Signed Harvest Manifest.

Guarantees data integrity between the untrusted internet ingress worker
and the quarantine/airlock gateway via SHA-256 content verification and HMAC signatures.
"""

from typing import List, Dict, Any, Optional
import hmac
import hashlib
import json
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class ManifestEntry(BaseModel):
    """File record within the signed harvest manifest."""
    paper_id: str
    title: str
    doi: Optional[str] = None
    queue: str  # "priority" or "archive"
    triage_score: float
    source: str
    pdf_filename: Optional[str] = None
    pdf_sha256: Optional[str] = None
    pdf_size_bytes: int = 0
    download_status: str = "pending"  # "pending", "downloaded", "failed"


class HarvestManifest(BaseModel):
    """Manifest container produced by Ingress and verified by Airlock."""
    harvest_id: str
    query: str
    expanded_terms: List[str] = Field(default_factory=list)
    created_at_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    total_papers: int = 0
    priority_count: int = 0
    archive_count: int = 0
    entries: List[ManifestEntry] = Field(default_factory=list)
    signature: Optional[str] = None

    @classmethod
    def create(
        cls,
        harvest_id: str,
        query: str,
        expanded_terms: List[str],
        entries: List[ManifestEntry],
        signing_key: Optional[bytes] = None,
    ) -> "HarvestManifest":
        """Instantiates and signs a new harvest manifest."""
        priority_n = sum(1 for e in entries if e.queue == "priority")
        archive_n = sum(1 for e in entries if e.queue == "archive")

        manifest = cls(
            harvest_id=harvest_id,
            query=query,
            expanded_terms=expanded_terms,
            total_papers=len(entries),
            priority_count=priority_n,
            archive_count=archive_n,
            entries=entries,
        )

        if signing_key:
            manifest.signature = manifest.compute_signature(signing_key)
        return manifest

    def _canonical_bytes(self) -> bytes:
        """Serializes payload deterministically without signature for hashing."""
        data = {
            "harvest_id": self.harvest_id,
            "query": self.query,
            "expanded_terms": sorted(self.expanded_terms),
            "created_at_utc": self.created_at_utc,
            "total_papers": self.total_papers,
            "priority_count": self.priority_count,
            "archive_count": self.archive_count,
            "entries": [e.model_dump() for e in sorted(self.entries, key=lambda x: x.paper_id)],
        }
        return json.dumps(data, sort_keys=True).encode("utf-8")

    def compute_signature(self, secret_key: bytes) -> str:
        """Computes HMAC-SHA256 signature over canonical bytes."""
        return hmac.new(secret_key, self._canonical_bytes(), hashlib.sha256).hexdigest()

    def verify_signature(self, secret_key: bytes) -> bool:
        """Verifies integrity and authenticity of the manifest."""
        if not self.signature:
            return False
        expected = self.compute_signature(secret_key)
        return hmac.compare_digest(self.signature, expected)

    def verify_file_integrity(self, file_path: str, expected_sha256: str) -> bool:
        """Verifies that a downloaded PDF matches its manifest SHA-256 hash."""
        try:
            h = hashlib.sha256()
            with open(file_path, "rb") as f:
                while chunk := f.read(65536):
                    h.update(chunk)
            return h.hexdigest().lower() == expected_sha256.lower()
        except Exception:
            return False
