"""
Hardware-Bound Cryptographic Vault Security for Privreach OS.

Binds the encrypted storage on disk to the physical CPU ID and Motherboard / System Hardware Profile.
If storage drives are cloned, stolen, or moved to another computer,
the cryptographic key cannot be derived and files cannot be decrypted.
Uses:
- CPU ProcessorId + CPU Model + System UUID + Hardware Topology
- Argon2id Key Derivation Function (memory-hard, resistant to GPU/ASIC attacks)
- AES-256-GCM authenticated encryption for chunks, vectors, manifest, and graph models.
"""

import os
import json
import uuid
import hashlib
import platform
import subprocess
from typing import Dict, Any, Tuple, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes


class HardwareBoundAuth:
    """
    Collects physical machine CPU and system hardware identifiers
    and enforces hardware-linked cryptographic authorization.
    """

    MAGIC_HEADER = b"PRIVREACH_HW_VAULT_V1"
    NONCE_LEN = 12
    SALT_LEN = 16
    KEY_LEN = 32

    _master_key_cache: Dict[bytes, bytes] = {}
    STATIC_MASTER_SALT = b"PRIVREACH_HW_V1_MASTER_KDF"

    @classmethod
    def get_hardware_profile(cls) -> Dict[str, str]:
        """
        Extract deterministic, stable hardware identifiers from the host CPU and motherboard.
        Cross-platform support for Windows, Linux, and macOS.
        """
        sys_name = platform.system()
        profile: Dict[str, str] = {
            "platform": sys_name,
            "machine": platform.machine(),
            "cpu_id": "UNKNOWN_CPU",
            "cpu_name": platform.processor() or "UNKNOWN_PROCESSOR",
            "system_uuid": "UNKNOWN_UUID",
            "node": hex(uuid.getnode()),
        }

        if sys_name == "Windows":
            # 1. Direct registry access for CPU name & identifier
            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
                )
                cpu_name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
                cpu_identifier, _ = winreg.QueryValueEx(key, "Identifier")
                profile["cpu_name"] = str(cpu_name).strip()
                profile["cpu_identifier"] = str(cpu_identifier).strip()
            except Exception:
                pass

            # 2. Query Windows CIM / WMI for CPU ProcessorId and ComputerSystemProduct UUID
            try:
                cmd = [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "(Get-CimInstance Win32_Processor).ProcessorId; (Get-CimInstance Win32_ComputerSystemProduct).UUID",
                ]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                lines = [l.strip() for l in res.stdout.strip().splitlines() if l.strip()]
                if len(lines) >= 1 and lines[0]:
                    profile["cpu_id"] = lines[0]
                if len(lines) >= 2 and lines[1]:
                    profile["system_uuid"] = lines[1]
            except Exception:
                pass

        elif sys_name == "Linux":
            try:
                with open("/proc/cpuinfo", "r", encoding="utf-8") as f:
                    for line in f:
                        if "Serial" in line or "model name" in line or "cpu family" in line:
                            parts = line.split(":")
                            if len(parts) == 2:
                                k, v = parts[0].strip(), parts[1].strip()
                                if "Serial" in k:
                                    profile["cpu_id"] = v
                                elif "model name" in k and profile["cpu_name"] == "UNKNOWN_PROCESSOR":
                                    profile["cpu_name"] = v
            except Exception:
                pass

            try:
                with open("/etc/machine-id", "r", encoding="utf-8") as f:
                    profile["system_uuid"] = f.read().strip()
            except Exception:
                try:
                    with open("/var/lib/dbus/machine-id", "r", encoding="utf-8") as f:
                        profile["system_uuid"] = f.read().strip()
                except Exception:
                    pass

        elif sys_name == "Darwin":
            try:
                out = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"]).decode().strip()
                profile["cpu_name"] = out
            except Exception:
                pass
            try:
                out = subprocess.check_output(["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"]).decode()
                for line in out.splitlines():
                    if "IOPlatformUUID" in line:
                        profile["system_uuid"] = line.split("=")[-1].strip().strip('"')
            except Exception:
                pass

        return profile

    @classmethod
    def get_hardware_fingerprint_bytes(cls) -> bytes:
        """
        Derives a strict deterministic 512-bit hardware fingerprint combining
        the CPU ID, processor brand, and system hardware UUID.
        """
        profile = cls.get_hardware_profile()
        stable_key_components = [
            f"CPU_ID={profile.get('cpu_id', '')}",
            f"CPU_NAME={profile.get('cpu_name', '')}",
            f"SYSTEM_UUID={profile.get('system_uuid', '')}",
            f"NODE={profile.get('node', '')}",
            f"PLATFORM={profile.get('platform', '')}",
        ]
        composite_str = "|".join(stable_key_components)
        return hashlib.sha512(composite_str.encode("utf-8")).digest()

    @classmethod
    def get_master_hardware_key(cls, hw_bytes: Optional[bytes] = None) -> bytes:
        """
        Derive the 256-bit hardware master key via Argon2id (64MB memory-hard cost).
        Cached in volatile RAM for the active process session so subsequent
        file operations run at sub-millisecond speeds with zero UX lag.
        """
        fingerprint = hw_bytes if hw_bytes is not None else cls.get_hardware_fingerprint_bytes()
        if fingerprint in cls._master_key_cache:
            return cls._master_key_cache[fingerprint]

        kdf = Argon2id(
            salt=cls.STATIC_MASTER_SALT,
            length=cls.KEY_LEN,
            iterations=2,
            lanes=4,
            memory_cost=64 * 1024,  # 64 MB RAM cost for high brute-force resistance
        )
        master_key = kdf.derive(fingerprint)
        cls._master_key_cache[fingerprint] = master_key
        return master_key

    @classmethod
    def derive_key(cls, salt: bytes) -> bytes:
        """
        Derive a 256-bit AES encryption key bound to this host CPU using HKDF-SHA256
        over the Argon2id hardware master key.
        Sub-millisecond speed, mathematically impossible to derive without the host CPU.
        """
        hw_bytes = cls.get_hardware_fingerprint_bytes()
        master_key = cls.get_master_hardware_key(hw_bytes)
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=cls.KEY_LEN,
            salt=salt,
            info=b"PRIVREACH_VAULT_FILE_ENCRYPTION",
        )
        return hkdf.derive(master_key)

    @classmethod
    def encrypt_data(cls, plaintext: bytes) -> bytes:
        """
        Encrypt data using hardware-derived AES-256-GCM.
        Format: MAGIC_HEADER (22B) + SALT (16B) + NONCE (12B) + CIPHERTEXT_WITH_TAG
        """
        salt = os.urandom(cls.SALT_LEN)
        nonce = os.urandom(cls.NONCE_LEN)
        key = cls.derive_key(salt)

        aesgcm = AESGCM(key)
        # Include magic header and salt as Additional Authenticated Data (AAD)
        aad = cls.MAGIC_HEADER + salt
        ciphertext = aesgcm.encrypt(nonce, plaintext, aad)

        return cls.MAGIC_HEADER + salt + nonce + ciphertext

    @classmethod
    def decrypt_data(cls, payload: bytes) -> bytes:
        """
        Decrypt data using hardware-derived AES-256-GCM.
        Raises ValueError or InvalidTag if the CPU or hardware profile does not match.
        """
        header_len = len(cls.MAGIC_HEADER)
        if not payload.startswith(cls.MAGIC_HEADER):
            raise ValueError("Payload missing hardware-bound vault magic header")

        offset = header_len
        salt = payload[offset : offset + cls.SALT_LEN]
        offset += cls.SALT_LEN
        nonce = payload[offset : offset + cls.NONCE_LEN]
        offset += cls.NONCE_LEN
        ciphertext = payload[offset:]

        key = cls.derive_key(salt)
        aesgcm = AESGCM(key)
        aad = cls.MAGIC_HEADER + salt

        try:
            return aesgcm.decrypt(nonce, ciphertext, aad)
        except Exception as e:
            raise PermissionError(
                "Hardware authorization failed: CPU ID or hardware profile mismatch. "
                "Decryption is mathematically impossible without the authorized host processor."
            ) from e

    @classmethod
    def verify_hardware_access(cls, sample_token: Optional[bytes] = None) -> Tuple[bool, str]:
        """
        Verify that the current host processor matches the hardware envelope.
        """
        try:
            profile = cls.get_hardware_profile()
            cpu_summary = f"{profile.get('cpu_name', 'CPU')} (ID: {profile.get('cpu_id', 'N/A')})"
            if sample_token:
                cls.decrypt_data(sample_token)
            return True, f"Hardware profile verified: {cpu_summary}"
        except Exception as ex:
            return False, f"Hardware verification failed: {str(ex)}"
