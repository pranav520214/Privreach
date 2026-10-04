"""Privearch Over-The-Air (OTA) Update System."""

from privearch.updater.version import VERSION, BUILD_CHANNEL, RELEASE_DATE, DEFAULT_OTA_MANIFEST_URL
from privearch.updater.ota_manager import OTAManager

__all__ = ["VERSION", "BUILD_CHANNEL", "RELEASE_DATE", "DEFAULT_OTA_MANIFEST_URL", "OTAManager"]
