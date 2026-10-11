"""
Unit and integration tests for Privreach OS Hardware-Bound Authentication and Cryptographic Vault.
Validates CPU ID binding, Argon2id key derivation, AES-256-GCM authenticated encryption,
and prevention of data leakage when storage drives are cloned or stolen.
"""

import os
import shutil
import tempfile
import pytest
import numpy as np
from unittest.mock import patch

from privreach.compute.hardware_auth import HardwareBoundAuth
from privreach.os_engine import PrivreachKernel
from privreach.schemas import DocumentChunk


def test_get_hardware_profile():
    profile = HardwareBoundAuth.get_hardware_profile()
    assert isinstance(profile, dict)
    assert "platform" in profile
    assert "cpu_id" in profile
    assert "cpu_name" in profile
    assert "system_uuid" in profile
    assert "node" in profile
    assert len(profile["cpu_id"]) > 0
    assert len(profile["cpu_name"]) > 0


def test_hardware_fingerprint_deterministic():
    fp1 = HardwareBoundAuth.get_hardware_fingerprint_bytes()
    fp2 = HardwareBoundAuth.get_hardware_fingerprint_bytes()
    assert fp1 == fp2
    assert len(fp1) == 64  # SHA-512


def test_encryption_and_decryption_roundtrip():
    original_data = b"Confidential scientific derivation: E = mc^2 and aerodynamic lift equations."
    encrypted = HardwareBoundAuth.encrypt_data(original_data)

    assert encrypted.startswith(HardwareBoundAuth.MAGIC_HEADER)
    assert len(encrypted) > len(original_data) + len(HardwareBoundAuth.MAGIC_HEADER)

    decrypted = HardwareBoundAuth.decrypt_data(encrypted)
    assert decrypted == original_data


def test_decrypt_fails_with_foreign_cpu_id():
    """
    Simulates physical storage drive theft:
    Files encrypted on the authorized CPU are placed on an unauthorized machine with a different CPU ID.
    Decryption must fail with PermissionError.
    """
    secret = b"Top Secret Research Dataset - Proprietary Propulsion Model"
    encrypted = HardwareBoundAuth.encrypt_data(secret)

    # Simulate foreign CPU ID / motherboard fingerprint
    foreign_fingerprint = b"FOREIGN_ATTACKER_CPU_FINGERPRINT_1234567890_NOT_AUTHORIZED_HOST_0000"
    with patch.object(HardwareBoundAuth, "get_hardware_fingerprint_bytes", return_value=foreign_fingerprint):
        with pytest.raises(PermissionError) as exc_info:
            HardwareBoundAuth.decrypt_data(encrypted)
        assert "Hardware authorization failed: CPU ID or hardware profile mismatch" in str(exc_info.value)


def test_decrypt_fails_with_tampered_ciphertext():
    data = b"Airfoil Reynolds Number: 1.25e6"
    encrypted = bytearray(HardwareBoundAuth.encrypt_data(data))
    # Corrupt a byte in the ciphertext payload
    encrypted[-5] ^= 0xFF

    with pytest.raises(PermissionError):
        HardwareBoundAuth.decrypt_data(bytes(encrypted))


def test_decrypt_fails_without_magic_header():
    with pytest.raises(ValueError) as exc_info:
        HardwareBoundAuth.decrypt_data(b"INVALID_HEADER_DATA_12345")
    assert "missing hardware-bound vault magic header" in str(exc_info.value)


def test_verify_hardware_access():
    verified, msg = HardwareBoundAuth.verify_hardware_access()
    assert verified is True
    assert "Hardware profile verified" in msg


def test_os_engine_hardware_vault_persistence_and_anti_theft():
    temp_dir = tempfile.mkdtemp(prefix="privreach_hw_test_")
    try:
        kernel = PrivreachKernel()
        # Clear in-RAM index to ensure pure isolation for test
        kernel.clear_index(delete_cache_files=False)
        kernel.cache_dir = temp_dir

        # Create a sample chunk
        chunk = DocumentChunk(
            chunk_id="test-chunk-1",
            doc_name="hypersonic_flow.pdf",
            page_num=1,
            text="Hypersonic boundary layer transition occurs at Mach numbers exceeding 5.0.",
            word_count=12,
            evidence_type="PROSE",
        )
        fake_vector = np.array([[0.1, 0.2, 0.3]], dtype=np.float32)

        kernel.bm25.add_chunks([chunk])
        kernel.vector_index.add_vectors(fake_vector, [chunk])
        kernel.total_chunks = 1
        kernel.ingested_files = [{"doc_name": "hypersonic_flow.pdf", "path": "/fake/hypersonic_flow.pdf", "chunks": 1}]

        # 1. Save index with hardware-bound encryption
        saved = kernel.save_index(temp_dir)
        assert saved is True

        # Verify encrypted vault files exist and start with MAGIC_HEADER
        for vfile in ["chunks.vault", "vectors.vault", "manifest.vault", "graph.vault"]:
            vpath = os.path.join(temp_dir, vfile)
            assert os.path.exists(vpath), f"Expected {vfile} to exist"
            with open(vpath, "rb") as f:
                header = f.read(len(HardwareBoundAuth.MAGIC_HEADER))
                assert header == HardwareBoundAuth.MAGIC_HEADER, f"{vfile} must start with MAGIC_HEADER"

        # Verify plaintext files do NOT exist on disk
        for pfile in ["chunks.json", "vectors.npy", "manifest.json", "graph.json"]:
            ppath = os.path.join(temp_dir, pfile)
            assert not os.path.exists(ppath), f"Plaintext {pfile} must not leak on disk"

        # 2. Wipe in-RAM state and reload from the encrypted vault on authorized CPU
        kernel.clear_index(delete_cache_files=False)
        assert kernel.total_chunks == 0

        loaded = kernel.load_index(temp_dir)
        assert loaded is True
        assert kernel.total_chunks == 1
        assert len(kernel.bm25.chunks) == 1
        assert kernel.bm25.chunks[0].chunk_id == "test-chunk-1"
        assert kernel.vector_index.vectors is not None
        assert kernel.vector_index.vectors.shape == (1, 3)

        # 3. Simulate stolen drive scenario on an unauthorized foreign machine
        foreign_fingerprint = b"FOREIGN_STOLEN_DRIVE_ATTACKER_CPU_778899"
        with patch.object(HardwareBoundAuth, "get_hardware_fingerprint_bytes", return_value=foreign_fingerprint):
            with pytest.raises(PermissionError):
                kernel.load_index(temp_dir)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
