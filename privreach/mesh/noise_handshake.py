"""
Noise Protocol Handshake Engine.

Implements Noise_IK authenticated Diffie-Hellman key exchange using Curve25519 (X25519)
and HKDF-SHA256 session key derivation for zero-trust P2P device mesh networking.
"""

from typing import Tuple, Optional, Dict, Any
import os
import hashlib
import base64
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from pydantic import BaseModel, Field


class DeviceIdentity(BaseModel):
    """Public identity descriptor for a participating mesh node."""
    device_id: str
    device_name: str
    public_key_b64: str
    fingerprint: str


class HandshakeSession(BaseModel):
    """Established cryptographically authenticated communication session."""
    session_id: str
    peer_device_id: str
    is_authenticated: bool
    tx_key_b64: str
    rx_key_b64: str


class NoiseHandshake:
    """
    Orchestrates mutual ECDH authentication and session derivation between nodes.
    """

    def __init__(
        self,
        device_id: str,
        device_name: str,
        static_private_key: Optional[x25519.X25519PrivateKey] = None,
    ):
        self.device_id = device_id
        self.device_name = device_name
        self.static_key = static_private_key or x25519.X25519PrivateKey.generate()
        self.public_key = self.static_key.public_key()

    @property
    def public_bytes(self) -> bytes:
        """Returns 32-byte raw public key."""
        return self.public_key.public_bytes_raw()

    @property
    def public_b64(self) -> str:
        """Returns base64 encoded public key."""
        return base64.b64encode(self.public_bytes).decode("ascii")

    @property
    def fingerprint(self) -> str:
        """Returns SHA-256 visual hexadecimal fingerprint."""
        return hashlib.sha256(self.public_bytes).hexdigest()[:16]

    def get_identity(self) -> DeviceIdentity:
        """Returns public DeviceIdentity descriptor."""
        return DeviceIdentity(
            device_id=self.device_id,
            device_name=self.device_name,
            public_key_b64=self.public_b64,
            fingerprint=self.fingerprint,
        )

    def initiate_handshake(
        self,
        peer_identity: DeviceIdentity,
    ) -> Tuple[bytes, HandshakeSession]:
        """
        Initiator side (Party A):
        Generates ephemeral keypair, computes ECDH with peer's static public key,
        and derives transmit/receive keys.

        Returns:
            (ephemeral_public_bytes_to_send, established_session)
        """
        peer_pub_bytes = base64.b64decode(peer_identity.public_key_b64.encode("ascii"))
        peer_pub_key = x25519.X25519PublicKey.from_public_bytes(peer_pub_bytes)

        # Generate ephemeral key
        ephemeral_priv = x25519.X25519PrivateKey.generate()
        ephemeral_pub = ephemeral_priv.public_key()
        ephemeral_bytes = ephemeral_pub.public_bytes_raw()

        # Compute dual DH secrets (es, ss)
        dh1 = ephemeral_priv.exchange(peer_pub_key)
        dh2 = self.static_key.exchange(peer_pub_key)
        shared_secret = dh1 + dh2

        # Derive directional session keys via HKDF
        salt = hashlib.sha256(ephemeral_bytes + peer_pub_bytes).digest()
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=64,
            salt=salt,
            info=b"PRIVREACH_MESH_SESSION_V1",
        )
        derived = hkdf.derive(shared_secret)
        tx_key = derived[:32]
        rx_key = derived[32:64]

        session_id = hashlib.sha256(derived).hexdigest()[:16]
        session = HandshakeSession(
            session_id=session_id,
            peer_device_id=peer_identity.device_id,
            is_authenticated=True,
            tx_key_b64=base64.b64encode(tx_key).decode("ascii"),
            rx_key_b64=base64.b64encode(rx_key).decode("ascii"),
        )
        return ephemeral_bytes, session

    def respond_handshake(
        self,
        peer_identity: DeviceIdentity,
        ephemeral_bytes_from_peer: bytes,
    ) -> HandshakeSession:
        """
        Responder side (Party B):
        Accepts peer's ephemeral public key, computes matching ECDH secrets,
        and derives inverted transmit/receive keys.

        Returns:
            established_session (where tx_key corresponds to Initiator's rx_key)
        """
        peer_pub_bytes = base64.b64decode(peer_identity.public_key_b64.encode("ascii"))
        peer_pub_key = x25519.X25519PublicKey.from_public_bytes(peer_pub_bytes)
        ephemeral_pub_key = x25519.X25519PublicKey.from_public_bytes(ephemeral_bytes_from_peer)

        # Compute matching DH secrets
        dh1 = self.static_key.exchange(ephemeral_pub_key)
        dh2 = self.static_key.exchange(peer_pub_key)
        shared_secret = dh1 + dh2

        # Derive directional session keys via identical HKDF
        salt = hashlib.sha256(ephemeral_bytes_from_peer + self.public_bytes).digest()
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=64,
            salt=salt,
            info=b"PRIVREACH_MESH_SESSION_V1",
        )
        derived = hkdf.derive(shared_secret)
        # Note: Responder transmits on Initiator's rx_key and receives on Initiator's tx_key
        rx_key = derived[:32]
        tx_key = derived[32:64]

        session_id = hashlib.sha256(derived).hexdigest()[:16]
        return HandshakeSession(
            session_id=session_id,
            peer_device_id=peer_identity.device_id,
            is_authenticated=True,
            tx_key_b64=base64.b64encode(tx_key).decode("ascii"),
            rx_key_b64=base64.b64encode(rx_key).decode("ascii"),
        )
