"""
Unit and Integration Tests for privreach.mesh multi-device synchronization.
"""

import unittest
from cryptography.exceptions import InvalidTag

from privreach.mesh.noise_handshake import NoiseHandshake
from privreach.mesh.xchacha_stream import StreamCipher
from privreach.mesh.qr_pairing import QRPairingEngine, PairingPayload
from privreach.mesh.merkle_sync import MerkleSyncTree


class TestMeshSubsystem(unittest.TestCase):
    """Verifies Noise handshake, ChaCha20Poly1305 AEAD, QR pairing, and Merkle tree sync."""

    def setUp(self):
        # Node A: Workstation
        self.node_a = NoiseHandshake(device_id="workstation_01", device_name="Lab Workstation")
        # Node B: Tablet
        self.node_b = NoiseHandshake(device_id="tablet_02", device_name="Field Tablet")

    def test_noise_handshake_session_establishment(self):
        """Parties A and B must establish mutually authenticated inverted session keys."""
        id_a = self.node_a.get_identity()
        id_b = self.node_b.get_identity()

        # Step 1: Node A initiates to Node B
        ephemeral_bytes, session_a = self.node_a.initiate_handshake(id_b)

        # Step 2: Node B responds
        session_b = self.node_b.respond_handshake(id_a, ephemeral_bytes)

        # Verification: Session IDs match
        self.assertEqual(session_a.session_id, session_b.session_id)
        self.assertTrue(session_a.is_authenticated)
        self.assertTrue(session_b.is_authenticated)

        # Crucial: Initiator's TX key must match Responder's RX key, and vice versa!
        self.assertEqual(session_a.tx_key_b64, session_b.rx_key_b64)
        self.assertEqual(session_a.rx_key_b64, session_b.tx_key_b64)

    def test_stream_cipher_encryption_and_decryption(self):
        """Ciphertexts encrypted with Party A TX key decrypt accurately with Party B RX key."""
        id_b = self.node_b.get_identity()
        ephemeral_bytes, session_a = self.node_a.initiate_handshake(id_b)
        session_b = self.node_b.respond_handshake(self.node_a.get_identity(), ephemeral_bytes)

        tx_cipher = StreamCipher.from_b64_key(session_a.tx_key_b64)
        rx_cipher = StreamCipher.from_b64_key(session_b.rx_key_b64)

        secret_payload = b"Vault chunk: EUV lithography numerical aperture = 0.55"
        packet = tx_cipher.encrypt_bytes(secret_payload)

        # Decrypt on peer side
        decrypted = rx_cipher.decrypt_packet(packet)
        self.assertEqual(decrypted, secret_payload)

    def test_stream_cipher_tamper_detection(self):
        """Tampered ciphertext must fail Poly1305 MAC verification."""
        id_b = self.node_b.get_identity()
        ephemeral_bytes, session_a = self.node_a.initiate_handshake(id_b)
        session_b = self.node_b.respond_handshake(self.node_a.get_identity(), ephemeral_bytes)

        tx_cipher = StreamCipher.from_b64_key(session_a.tx_key_b64)
        rx_cipher = StreamCipher.from_b64_key(session_b.rx_key_b64)

        packet = tx_cipher.encrypt_bytes(b"Clean experimental data")
        # Tamper with the ciphertext payload
        tampered_bytes = bytearray(packet.ciphertext_b64.encode("ascii"))
        tampered_bytes[10] = ord("Z") if tampered_bytes[10] != ord("Z") else ord("A")
        packet.ciphertext_b64 = tampered_bytes.decode("ascii")

        with self.assertRaises(Exception):
            rx_cipher.decrypt_packet(packet)

    def test_qr_pairing_uri_and_enrollment(self):
        """QR pairing URI generation, parsing, and peer authorization."""
        pairing_engine_a = QRPairingEngine(self.node_a.get_identity())
        invitation = pairing_engine_a.create_pairing_invitation()

        # Convert to URI format
        uri_str = invitation.to_uri()
        self.assertTrue(uri_str.startswith("privreach://mesh/pair?"))

        # Node B parses URI from QR scan
        parsed_invitation = PairingPayload.from_uri(uri_str)
        self.assertEqual(parsed_invitation.device_id, "workstation_01")
        self.assertEqual(parsed_invitation.fingerprint, self.node_a.fingerprint)

        # Enroll peer
        pairing_engine_b = QRPairingEngine(self.node_b.get_identity())
        enrolled_dev = pairing_engine_b.enroll_peer_from_payload(parsed_invitation)

        self.assertEqual(enrolled_dev.device_id, "workstation_01")
        self.assertTrue(pairing_engine_b.is_peer_authorized("workstation_01"))

    def test_merkle_sync_identical_and_deltas(self):
        """Merkle tree computes O(log N) deltas between distinct device vaults."""
        tree_a = MerkleSyncTree()
        tree_b = MerkleSyncTree()

        # Add identical items to both trees
        tree_a.add_item("doc_01", b"Content of paper 1")
        tree_a.add_item("doc_02", b"Content of paper 2")
        tree_b.add_item("doc_01", b"Content of paper 1")
        tree_b.add_item("doc_02", b"Content of paper 2")

        # Initial check: Trees must be 100% identical
        delta_init = tree_a.compute_delta(tree_b)
        self.assertTrue(delta_init.is_identical)
        self.assertEqual(len(delta_init.missing_in_remote), 0)

        # Add new item to Node A
        tree_a.add_item("doc_03", b"Content of paper 3 on Node A")
        delta_updated = tree_a.compute_delta(tree_b)

        self.assertFalse(delta_updated.is_identical)
        self.assertIn("doc_03", delta_updated.missing_in_remote)
        self.assertEqual(len(delta_updated.missing_in_local), 0)

        # Modify item on Node B
        tree_b.add_item("doc_01", b"Altered version of paper 1 on Node B")
        delta_diff = tree_a.compute_delta(tree_b)

        self.assertFalse(delta_diff.is_identical)
        self.assertIn("doc_01", delta_diff.modified_items)


if __name__ == "__main__":
    unittest.main()
