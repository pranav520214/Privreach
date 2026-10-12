"""
Temporal Correlator and Multimodal Experiment Ledger.

Aligns nanosecond-resolution sensor readings with computer vision actions,
optical gauge reads, and transcribed audio narration into a unified chronological ledger.
"""

from typing import List, Dict, Tuple, Optional, Any
import time
from pydantic import BaseModel, Field

from privreach.lab.ring_buffer import TelemetryRingBuffer, TelemetrySample


class CorrelatedExperimentEvent(BaseModel):
    """An aligned multimodal event linking action/speech with physical sensor telemetry."""
    event_id: str
    timestamp_ns: int
    event_type: str  # "VISION_ACTION", "AUDIO_NOTE", "GAUGE_READING", "SENSOR_ANOMALY"
    description: str
    sensor_snapshot: Dict[str, float] = Field(default_factory=dict)
    sensor_units: Dict[str, str] = Field(default_factory=dict)


class TemporalCorrelator:
    """
    Correlates discrete events with continuous background sensor time-series.
    """

    def __init__(self, ring_buffer: TelemetryRingBuffer):
        self.ring_buffer = ring_buffer
        self.events: List[CorrelatedExperimentEvent] = []

    def record_event(
        self,
        event_type: str,
        description: str,
        timestamp_ns: Optional[int] = None,
        window_tolerance_ns: int = 2_000_000_000,  # 2 seconds window for sensor correlation
    ) -> CorrelatedExperimentEvent:
        """
        Records an event and snapshots the most recent sensor values surrounding that timestamp.
        """
        ts = timestamp_ns if timestamp_ns is not None else time.time_ns()

        # Query surrounding sensor samples from ring buffer
        start_ns = ts - window_tolerance_ns
        end_ns = ts + window_tolerance_ns
        samples = self.ring_buffer.read_time_window(start_ns, end_ns)

        # Snapshot the most temporally proximal sample per channel
        snapshot: Dict[str, float] = {}
        units: Dict[str, str] = {}

        channel_samples: Dict[str, List[TelemetrySample]] = {}
        for s in samples:
            channel_samples.setdefault(s.channel_id, []).append(s)

        for ch_id, ch_list in channel_samples.items():
            # Closest in time to event timestamp ts
            closest = min(ch_list, key=lambda x: abs(x.timestamp_ns - ts))
            snapshot[ch_id] = closest.value
            units[ch_id] = closest.unit

        event_id = f"evt_{len(self.events) + 1:04d}"
        corr_event = CorrelatedExperimentEvent(
            event_id=event_id,
            timestamp_ns=ts,
            event_type=event_type,
            description=description,
            sensor_snapshot=snapshot,
            sensor_units=units,
        )
        self.events.append(corr_event)
        return corr_event

    def query_events(self, query: str) -> List[CorrelatedExperimentEvent]:
        """
        Searches recorded events by keyword in description or event type.
        """
        q_norm = query.strip().lower()
        matched: List[CorrelatedExperimentEvent] = []
        for e in self.events:
            if q_norm in e.description.lower() or q_norm in e.event_type.lower():
                matched.append(e)
        return matched
