"""
Out-of-Band QR Code and URI Device Pairing Engine.

Facilitates zero-trust physical pairing between researcher devices
(phone, tablet, laptop) using visual QR code / URI key material transfer.
"""

from typing import List, Dict, Optional, Tuple, Any
import urllib.parse
import hashlib
import json
import base64
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from privreach.mesh.noise_handshake import DeviceIdentity


class PairingPayload(BaseModel):
    """Pairing descriptor suitable for encoding into a QR code image or deep link."""
    pairing_id: str
    device_id: str
    device_name: str
    public_key_b64: str
    fingerprint: str
    ephemeral_nonce: str
    created_at_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_uri(self) -> str:
        """Serializes payload into a standardized privreach:// deep-link URI."""
        params = {
            "pid": self.pairing_id,
            "id": self.device_id,
            "name": self.device_name,
            "pk": self.public_key_b64,
            "fp": self.fingerprint,
            "nonce": self.ephemeral_nonce,
        }
        return f"privreach://mesh/pair?{urllib.parse.urlencode(params)}"

    @classmethod
    def from_uri(cls, uri_str: str) -> "PairingPayload":
        """Parses a privreach:// pairing URI."""
        parsed = urllib.parse.urlparse(uri_str)
        qs = urllib.parse.parse_qs(parsed.query)

        return cls(
            pairing_id=qs.get("pid", [""])[0],
            device_id=qs.get("id", [""])[0],
            device_name=qs.get("name", [""])[0],
            public_key_b64=qs.get("pk", [""])[0],
            fingerprint=qs.get("fp", [""])[0],
            ephemeral_nonce=qs.get("nonce", [""])[0],
        )


class PairedDevice(BaseModel):
    """Record of an authorized paired peer node."""
    device_id: str
    device_name: str
    public_key_b64: str
    fingerprint: str
    paired_at_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_seen_utc: Optional[str] = None
    trust_level: str = "TRUSTED"  # TRUSTED, REVOKED


class QRPairingEngine:
    """
    Manages pairing invitation generation, scanning, and mutual device enrollment.
    """

    def __init__(self, local_identity: DeviceIdentity):
        self.local_identity = local_identity
        self.paired_devices: Dict[str, PairedDevice] = {}

    def create_pairing_invitation(self) -> PairingPayload:
        """
        Generates an ephemeral pairing token to display as a QR code.
        """
        nonce = base64.b64encode(hashlib.sha256(self.local_identity.public_key_b64.encode("ascii")).digest()[:16]).decode("ascii")
        pairing_id = f"pair_{hashlib.sha256(nonce.encode('ascii')).hexdigest()[:8]}"

        return PairingPayload(
            pairing_id=pairing_id,
            device_id=self.local_identity.device_id,
            device_name=self.local_identity.device_name,
            public_key_b64=self.local_identity.public_key_b64,
            fingerprint=self.local_identity.fingerprint,
            ephemeral_nonce=nonce,
        )

    def enroll_peer_from_payload(self, payload: PairingPayload) -> PairedDevice:
        """
        Validates scanned pairing payload and enrolls remote device into authorized mesh registry.
        """
        # Validate that fingerprint matches public key
        pub_bytes = base64.b64decode(payload.public_key_b64.encode("ascii"))
        computed_fp = hashlib.sha256(pub_bytes).hexdigest()[:16]

        if computed_fp != payload.fingerprint:
            raise ValueError(f"Fingerprint mismatch: expected {payload.fingerprint}, computed {computed_fp}")

        device = PairedDevice(
            device_id=payload.device_id,
            device_name=payload.device_name,
            public_key_b64=payload.public_key_b64,
            fingerprint=payload.fingerprint,
        )
        self.paired_devices[device.device_id] = device
        return device

    def is_peer_authorized(self, device_id: str) -> bool:
        """Returns True if peer is registered and has TRUSTED status."""
        peer = self.paired_devices.get(device_id)
        return peer is not None and peer.trust_level == "TRUSTED"
