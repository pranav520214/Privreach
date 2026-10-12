"""
privreach.lab: High-Frequency Live Laboratory Experiment Telemetry Subsystem.

Responsible for:
- Memory-mapped lock-free telemetry circular ring buffers
- Multi-channel physical sensor ingestion and anomaly threshold detection
- Instrument display gauge OCR reading
- Nanosecond temporal correlation aligning sensor series, video events, and voice notes
"""

from privreach.lab.ring_buffer import TelemetryRingBuffer, TelemetrySample
from privreach.lab.sensor_ingest import SensorIngestEngine, SensorChannel, SensorAnomaly
from privreach.lab.ocr_reader import InstrumentOCRReader, GaugeReading
from privreach.lab.temporal_correlator import TemporalCorrelator, CorrelatedExperimentEvent

__all__ = [
    "TelemetryRingBuffer",
    "TelemetrySample",
    "SensorIngestEngine",
    "SensorChannel",
    "SensorAnomaly",
    "InstrumentOCRReader",
    "GaugeReading",
    "TemporalCorrelator",
    "CorrelatedExperimentEvent",
]
