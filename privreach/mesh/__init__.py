"""
privreach.mesh: Multi-Device Encrypted P2P Mesh Subsystem.

Responsible for:
- Noise_IK Diffie-Hellman handshake over Curve25519 (X25519)
- Authenticated stream encryption via ChaCha20-Poly1305 AEAD
- Out-of-band ephemeral device pairing (QR code / pairing URI)
- Merkle tree delta synchronization across local research enclaves
"""

from privreach.mesh.noise_handshake import NoiseHandshake, HandshakeSession, DeviceIdentity
from privreach.mesh.xchacha_stream import StreamCipher, EncryptedPacket
from privreach.mesh.qr_pairing import QRPairingEngine, PairingPayload, PairedDevice
from privreach.mesh.merkle_sync import MerkleSyncTree, MerkleNode, SyncDelta

__all__ = [
    "NoiseHandshake",
    "HandshakeSession",
    "DeviceIdentity",
    "StreamCipher",
    "EncryptedPacket",
    "QRPairingEngine",
    "PairingPayload",
    "PairedDevice",
    "MerkleSyncTree",
    "MerkleNode",
    "SyncDelta",
]
