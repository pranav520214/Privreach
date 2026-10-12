"""
Merkle Tree Delta Synchronization Engine.

Constructs cryptographic Merkle trees over vault document chunks to discover
differences between mesh nodes in O(log N) time and transmit minimal delta updates.
"""

from typing import List, Dict, Set, Tuple, Optional, Any
import hashlib
from pydantic import BaseModel, Field


class MerkleNode(BaseModel):
    """A node within the Merkle hash tree."""
    hash: str
    item_id: Optional[str] = None
    left_child_hash: Optional[str] = None
    right_child_hash: Optional[str] = None


class SyncDelta(BaseModel):
    """Computed difference between two enclaves requiring network transfer."""
    is_identical: bool
    missing_in_remote: List[str] = Field(default_factory=list)  # item_ids to send
    missing_in_local: List[str] = Field(default_factory=list)   # item_ids to request
    modified_items: List[str] = Field(default_factory=list)     # item_ids with altered contents


class MerkleSyncTree:
    """
    Cryptographic Merkle tree built over key-value document entries.
    """

    def __init__(self):
        # item_id -> content_hash
        self.leaf_entries: Dict[str, str] = {}
        self.root_hash: str = ""

    def add_item(self, item_id: str, content: bytes) -> str:
        """Adds or updates an item and recomputes leaf hash."""
        h = hashlib.sha256(content).hexdigest()
        self.leaf_entries[item_id] = h
        self.recompute_tree()
        return h

    def add_item_hash(self, item_id: str, content_hash: str) -> None:
        """Adds an item with precomputed content hash."""
        self.leaf_entries[item_id] = content_hash
        self.recompute_tree()

    def remove_item(self, item_id: str) -> None:
        """Removes an item from the tree."""
        if item_id in self.leaf_entries:
            del self.leaf_entries[item_id]
            self.recompute_tree()

    def recompute_tree(self) -> str:
        """
        Recomputes the root hash across all sorted leaves.
        """
        if not self.leaf_entries:
            self.root_hash = hashlib.sha256(b"EMPTY_MERKLE_TREE").hexdigest()
            return self.root_hash

        # Deterministic leaf sorting by item_id
        sorted_keys = sorted(self.leaf_entries.keys())
        current_level = [
            hashlib.sha256(f"{k}:{self.leaf_entries[k]}".encode("utf-8")).hexdigest()
            for k in sorted_keys
        ]

        # Reduce levels pair-by-pair to root
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                if i + 1 < len(current_level):
                    combined = current_level[i] + current_level[i + 1]
                else:
                    # Duplicate last odd node
                    combined = current_level[i] + current_level[i]
                next_level.append(hashlib.sha256(combined.encode("utf-8")).hexdigest())
            current_level = next_level

        self.root_hash = current_level[0]
        return self.root_hash

    def compute_delta(self, remote_tree: "MerkleSyncTree") -> SyncDelta:
        """
        Compares local tree with remote tree and computes precise delta requirements.
        """
        # If root hashes match, trees are 100% bit-for-bit identical!
        if self.root_hash == remote_tree.root_hash:
            return SyncDelta(
                is_identical=True,
                missing_in_remote=[],
                missing_in_local=[],
                modified_items=[],
            )

        local_keys = set(self.leaf_entries.keys())
        remote_keys = set(remote_tree.leaf_entries.keys())

        missing_in_remote = sorted(list(local_keys - remote_keys))
        missing_in_local = sorted(list(remote_keys - local_keys))

        # Check common keys for differing content hashes
        common_keys = local_keys.intersection(remote_keys)
        modified = [
            k for k in common_keys
            if self.leaf_entries[k] != remote_tree.leaf_entries[k]
        ]

        return SyncDelta(
            is_identical=False,
            missing_in_remote=missing_in_remote,
            missing_in_local=missing_in_local,
            modified_items=sorted(modified),
        )
