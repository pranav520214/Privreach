"""
Authenticated Stream Encryption using ChaCha20-Poly1305 AEAD.

Secures chunk synchronization frames and inter-device control messages
with 256-bit encryption and Poly1305 cryptographic message authentication codes.
"""

from typing import Optional, Dict, Any
import os
import base64
from datetime import datetime, timezone
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from pydantic import BaseModel, Field


class EncryptedPacket(BaseModel):
    """Authenticated ciphertext packet exchanged between mesh nodes."""
    packet_id: str
    nonce_b64: str
    ciphertext_b64: str
    timestamp_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class StreamCipher:
    """
    Encrypts and decrypts message streams using 256-bit symmetric session keys.
    """

    NONCE_LEN = 12

    def __init__(self, key: bytes):
        if len(key) != 32:
            raise ValueError(f"ChaCha20Poly1305 requires 32-byte key, got {len(key)}")
        self.key = key
        self.cipher = ChaCha20Poly1305(key)

    @classmethod
    def from_b64_key(cls, b64_key: str) -> "StreamCipher":
        """Instantiates cipher from a base64 encoded 32-byte key."""
        raw_key = base64.b64decode(b64_key.encode("ascii"))
        return cls(raw_key)

    def encrypt_bytes(self, plaintext: bytes, associated_data: Optional[bytes] = None) -> EncryptedPacket:
        """
        Encrypts raw bytes and emits EncryptedPacket with unique nonce and auth tag.
        """
        nonce = os.urandom(self.NONCE_LEN)
        ciphertext = self.cipher.encrypt(nonce, plaintext, associated_data)

        packet_id = base64.b64encode(os.urandom(8)).decode("ascii")
        return EncryptedPacket(
            packet_id=packet_id,
            nonce_b64=base64.b64encode(nonce).decode("ascii"),
            ciphertext_b64=base64.b64encode(ciphertext).decode("ascii"),
        )

    def decrypt_packet(self, packet: EncryptedPacket, associated_data: Optional[bytes] = None) -> bytes:
        """
        Decrypts an incoming EncryptedPacket and verifies Poly1305 MAC tag.
        Raises InvalidTag if tampered.
        """
        nonce = base64.b64decode(packet.nonce_b64.encode("ascii"))
        ciphertext = base64.b64decode(packet.ciphertext_b64.encode("ascii"))
        return self.cipher.decrypt(nonce, ciphertext, associated_data)
