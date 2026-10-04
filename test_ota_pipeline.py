"""Automated End-to-End Test for Privearch OTA Update Engine."""

import os
import sys
import json
import shutil
import tempfile

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from privearch.updater.version import VERSION
from privearch.updater.ota_manager import OTAManager, parse_semver, calculate_sha256


def test_ota():
    print("[TEST 1/5] Testing SemVer parsing...")
    assert parse_semver("1.0.0") == (1, 0, 0)
    assert parse_semver("v1.0.1") == (1, 0, 1)
    assert parse_semver("2.1.4") > parse_semver("1.9.9")
    print("  ✓ SemVer logic verified.")

    # Create temporary sandbox environment
    temp_dir = tempfile.mkdtemp(prefix="privearch_ota_test_")
    print(f"\n[SANDBOX] Initialized isolated test environment: {temp_dir}")

    try:
        source_dir = os.path.join(temp_dir, "install_root")
        os.makedirs(source_dir, exist_ok=True)

        # Create mock installation files
        os.makedirs(os.path.join(source_dir, "privearch"), exist_ok=True)
        with open(os.path.join(source_dir, "privearch", "core.py"), "w") as f:
            f.write("# v1.0.0 original code")
        
        # Create critical user vault cache (.privearch_cache) that MUST be preserved
        cache_dir = os.path.join(source_dir, ".privearch_cache")
        os.makedirs(cache_dir, exist_ok=True)
        with open(os.path.join(cache_dir, "vault_data.bin"), "w") as f:
            f.write("PROTECTED_CHEMISTRY_EMBEDDINGS_AND_TEXT_CHUNKS")

        # 2. Build mock v1.0.1 release update package
        print("\n[TEST 2/5] Creating OTA Update Bundle for v1.0.1...")
        release_staging = os.path.join(temp_dir, "release_staging")
        os.makedirs(os.path.join(release_staging, "privearch"), exist_ok=True)
        with open(os.path.join(release_staging, "privearch", "core.py"), "w") as f:
            f.write("# v1.0.1 updated code with new features!")
        with open(os.path.join(release_staging, "NEW_FEATURE.md"), "w") as f:
            f.write("# New feature documentation")

        # Attempt to maliciously include a .privearch_cache in update bundle
        # (The updater MUST protect the user's existing vault from being overwritten)
        bad_cache = os.path.join(release_staging, ".privearch_cache")
        os.makedirs(bad_cache, exist_ok=True)
        with open(os.path.join(bad_cache, "vault_data.bin"), "w") as f:
            f.write("MALICIOUS_OVERWRITE_ATTEMPT")

        bundle_zip = os.path.join(temp_dir, "privearch-update-v1.0.1.zip")
        import zipfile
        with zipfile.ZipFile(bundle_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(release_staging):
                for file in files:
                    full = os.path.join(root, file)
                    rel = os.path.relpath(full, release_staging)
                    zf.write(full, rel)

        manifest = {
            "version": "1.0.1",
            "release_date": "2026-10-04",
            "min_compatible_version": "1.0.0",
            "changelog": "- Added OTA Update Engine\n- Added High-Speed Local RLF Retuning",
            "download_url": bundle_zip,
            "sha256": calculate_sha256(bundle_zip)
        }

        manifest_path = os.path.join(temp_dir, "version.json")
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        print(f"  ✓ Bundle created: {bundle_zip}")
        print(f"  ✓ Manifest SHA256: {manifest['sha256']}")

        # 3. Test check_for_updates
        print("\n[TEST 3/5] Testing OTA update detection...")
        mgr = OTAManager(current_version="1.0.0", manifest_url=manifest_path, install_dir=source_dir)
        has_update, fetched_manifest, msg = mgr.check_for_updates()
        assert has_update is True
        assert fetched_manifest["version"] == "1.0.1"
        print(f"  ✓ Detected update: {msg}")

        # 4. Test download & SHA256 verification
        print("\n[TEST 4/5] Testing download and cryptographic verification...")
        success, downloaded_zip = mgr.download_update(fetched_manifest)
        assert success is True
        assert os.path.exists(downloaded_zip)
        print(f"  ✓ Successfully downloaded & verified SHA-256: {downloaded_zip}")

        # 5. Test atomic update application and vault preservation
        print("\n[TEST 5/5] Testing atomic update application & vault preservation...")
        app_success, app_msg = mgr.apply_update(downloaded_zip)
        assert app_success is True

        # Check updated file
        with open(os.path.join(source_dir, "privearch", "core.py"), "r") as f:
            core_content = f.read()
        assert "v1.0.1 updated code" in core_content

        # Check user vault preservation
        with open(os.path.join(source_dir, ".privearch_cache", "vault_data.bin"), "r") as f:
            vault_content = f.read()
        assert vault_content == "PROTECTED_CHEMISTRY_EMBEDDINGS_AND_TEXT_CHUNKS"
        print("  ✓ Core files successfully updated to v1.0.1!")
        print("  ✓ CRITICAL: .privearch_cache/ vault was 100% PRESERVED!")

        # Test Rollback
        print("\n[TEST BONUS] Testing automatic / manual rollback mechanism...")
        rb_success, rb_msg = mgr.rollback()
        assert rb_success is True
        with open(os.path.join(source_dir, "privearch", "core.py"), "r") as f:
            restored_core = f.read()
        assert "v1.0.0 original code" in restored_core
        print("  ✓ Rollback restored original v1.0.0 code seamlessly!")

        print("\n" + "=" * 70)
        print("🎉 ALL OTA ENGINE VERIFICATION TESTS PASSED SUCCESSFULLY!")
        print("=" * 70)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_ota()
