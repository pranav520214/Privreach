"""Artifact & Provenance Registry for Privreach: Tracking scientific artifacts and derivations."""

import os
import time
import json
import uuid
import hashlib
from typing import Dict, Any, List, Optional

from privearch.schemas import ArtifactRecord, ArtifactType


class ArtifactRegistry:
    """
    Manages generation, storage, and backward-provenance tracking
    for all scientific outputs produced by Privreach OS.
    
    Provenance Chain:
      Artifact -> Python Execution -> Equation -> Document -> Page
    """

    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = os.path.abspath(storage_dir or ".privearch_artifacts")
        os.makedirs(self.storage_dir, exist_ok=True)
        self.manifest_path = os.path.join(self.storage_dir, "artifacts_manifest.json")
        self._artifacts: Dict[str, ArtifactRecord] = {}
        self.load_manifest()

    def load_manifest(self) -> None:
        """Load artifact registry from disk if exists."""
        if os.path.exists(self.manifest_path):
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item in data.get("artifacts", []):
                    rec = ArtifactRecord(**item)
                    self._artifacts[rec.artifact_id] = rec
            except Exception as e:
                print(f"[Warning] Failed to load artifacts manifest: {e}")

    def save_manifest(self) -> None:
        """Save artifact records to disk."""
        data = {
            "total_artifacts": len(self._artifacts),
            "updated_at": time.time(),
            "artifacts": [rec.model_dump() for rec in self._artifacts.values()]
        }
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def register(self, record: ArtifactRecord) -> ArtifactRecord:
        """Register an artifact record into the ledger and save."""
        self._artifacts[record.artifact_id] = record
        self.save_manifest()
        return record

    def save_calculation(
        self,
        name: str,
        equation: str,
        variables: Dict[str, Any],
        computed_value: Any,
        code_executed: str,
        source_doc: str = "",
        source_page: Optional[int] = None,
        description: str = ""
    ) -> ArtifactRecord:
        """Create and persist a calculation artifact with complete provenance."""
        art_id = f"calc_{uuid.uuid4().hex[:8]}"
        file_name = f"{art_id}.json"
        file_path = os.path.join(self.storage_dir, file_name)

        payload = {
            "artifact_id": art_id,
            "name": name,
            "equation": equation,
            "variables": variables,
            "computed_value": computed_value,
            "code_executed": code_executed,
            "timestamp": time.time(),
            "source_doc": source_doc,
            "source_page": source_page
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        # Build provenance linkage
        code_hash = hashlib.sha256(code_executed.encode("utf-8")).hexdigest()[:12]
        provenance = {
            "source_document": source_doc,
            "source_page": source_page,
            "equation_formula": equation,
            "input_variables": variables,
            "execution_hash": code_hash,
            "tool_used": "privearch.compute.solver",
            "proof_chain": f"{source_doc} (p.{source_page}) -> {equation} -> {code_hash} -> {computed_value}"
        }

        record = ArtifactRecord(
            artifact_id=art_id,
            artifact_type=ArtifactType.CALCULATION,
            name=name,
            file_path=file_path,
            created_at=time.time(),
            description=description or f"Deterministic calculation of {name}",
            provenance=provenance,
            metadata={"computed_value": str(computed_value)}
        )

        return self.register(record)

    def save_plot(
        self,
        name: str,
        figure,
        description: str = "",
        provenance: Optional[Dict[str, Any]] = None
    ) -> ArtifactRecord:
        """Save a Matplotlib figure as an artifact with image file and provenance."""
        art_id = f"plot_{uuid.uuid4().hex[:8]}"
        file_name = f"{art_id}.png"
        file_path = os.path.join(self.storage_dir, file_name)

        figure.savefig(file_path, dpi=200, bbox_inches="tight")

        prov = provenance or {}
        prov.setdefault("tool_used", "matplotlib")
        prov.setdefault("format", "png")

        record = ArtifactRecord(
            artifact_id=art_id,
            artifact_type=ArtifactType.PLOT_2D,
            name=name,
            file_path=file_path,
            created_at=time.time(),
            description=description or f"2D scientific visualization of {name}",
            provenance=prov,
            metadata={"file_size_bytes": os.path.getsize(file_path)}
        )

        return self.register(record)

    def get(self, artifact_id: str) -> Optional[ArtifactRecord]:
        """Retrieve artifact record by ID."""
        return self._artifacts.get(artifact_id)

    def list_all(self) -> List[ArtifactRecord]:
        """List all registered artifacts ordered by newest first."""
        return sorted(self._artifacts.values(), key=lambda a: a.created_at, reverse=True)
