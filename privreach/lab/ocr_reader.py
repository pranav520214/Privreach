"""
Instrument Display and Digital Gauge OCR Reader.

Extracts physical measurements from optical image feeds of lab gauges,
multimeters, digital balances, and incubator displays.
"""

from typing import List, Dict, Tuple, Optional, Any
import re
import time
from pydantic import BaseModel, Field


class GaugeReading(BaseModel):
    """Reading parsed from a digital laboratory display."""
    device_label: str
    value: float
    unit: str = ""
    confidence: float = 1.0
    timestamp_ns: int
    raw_ocr_text: str = ""


class InstrumentOCRReader:
    """
    Parses digital readout strings and camera OCR crops into standardized numeric telemetry.
    """

    UNIT_PATTERNS = [
        (re.compile(r"(?:deg\s*c|°\s*c|celsius|(?<=\d)\s*c\b)", re.I), "degC"),
        (re.compile(r"(?:deg\s*k|kelvin|(?<=\d)\s*k\b)", re.I), "K"),
        (re.compile(r"\b(?:mpa|kpa|pa|bar|psi|mbar)\b", re.I), "bar"),
        (re.compile(r"\b(?:mg|kg|grams?)\b|(?<=\d)\s*g\b", re.I), "g"),
        (re.compile(r"\b(?:mv|volts?)\b|(?<=\d)\s*v\b", re.I), "V"),
        (re.compile(r"\b(?:ma|amps?)\b|(?<=\d)\s*a\b", re.I), "A"),
        (re.compile(r"\b(?:rpm)\b", re.I), "RPM"),
        (re.compile(r"\b(?:ph)\b", re.I), "pH"),
    ]

    def parse_display_text(
        self,
        text: str,
        device_label: str = "instrument_01",
        timestamp_ns: Optional[int] = None,
    ) -> Optional[GaugeReading]:
        """
        Extracts numbers and units from an OCR output string.
        """
        ts = timestamp_ns if timestamp_ns is not None else time.time_ns()
        clean = text.strip()

        # Extract unit
        detected_unit = ""
        for pattern, u_name in self.UNIT_PATTERNS:
            if pattern.search(clean):
                detected_unit = u_name
                break

        # Extract numeric value
        num_pattern = r"[-+]?(?:\d*\.\d+|\d+)"
        matches = re.findall(num_pattern, clean)
        if not matches:
            return None

        # Take first valid float match
        try:
            val = float(matches[0])
            confidence = 0.95 if detected_unit else 0.85
            return GaugeReading(
                device_label=device_label,
                value=val,
                unit=detected_unit,
                confidence=confidence,
                timestamp_ns=ts,
                raw_ocr_text=clean,
            )
        except Exception:
            return None
