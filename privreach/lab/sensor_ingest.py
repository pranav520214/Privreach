"""
Multi-Channel Sensor Ingestion and Anomaly Threshold Engine.

Registers physical sensor feeds (temperature, pressure, pH, spectrometer)
and triggers deterministic alerts upon safety threshold violations or rate spikes.
"""

from typing import List, Dict, Tuple, Optional, Any
from pydantic import BaseModel, Field

from privreach.lab.ring_buffer import TelemetryRingBuffer, TelemetrySample


class SensorChannel(BaseModel):
    """Specification of an active physical laboratory instrument channel."""
    channel_id: str
    name: str
    unit: str
    min_safe_threshold: Optional[float] = None
    max_safe_threshold: Optional[float] = None
    max_rate_of_change: Optional[float] = None  # maximum allowable delta per sample


class SensorAnomaly(BaseModel):
    """Event triggered upon abnormal telemetry reading."""
    anomaly_id: str
    channel_id: str
    anomaly_type: str  # "UPPER_THRESHOLD_BREACH", "LOWER_THRESHOLD_BREACH", "RATE_SPIKE"
    value: float
    threshold_limit: float
    timestamp_ns: int
    message: str


class SensorIngestEngine:
    """
    Ingests and monitors multi-channel laboratory sensor streams.
    """

    def __init__(self, ring_buffer: Optional[TelemetryRingBuffer] = None):
        self.ring_buffer = ring_buffer or TelemetryRingBuffer()
        self.channels: Dict[str, SensorChannel] = {}
        self.last_values: Dict[str, float] = {}
        self.anomalies: List[SensorAnomaly] = []

    def register_channel(
        self,
        channel_id: str,
        name: str,
        unit: str,
        min_safe: Optional[float] = None,
        max_safe: Optional[float] = None,
        max_rate_of_change: Optional[float] = None,
    ) -> SensorChannel:
        """Registers a sensor channel with optional safety guardrails."""
        channel = SensorChannel(
            channel_id=channel_id,
            name=name,
            unit=unit,
            min_safe_threshold=min_safe,
            max_safe_threshold=max_safe,
            max_rate_of_change=max_rate_of_change,
        )
        self.channels[channel_id] = channel
        return channel

    def ingest_reading(
        self,
        channel_id: str,
        value: float,
        timestamp_ns: Optional[int] = None,
    ) -> Tuple[TelemetrySample, Optional[SensorAnomaly]]:
        """
        Ingests a measurement, stores in ring buffer, and evaluates safety constraints.
        """
        channel = self.channels.get(channel_id)
        unit = channel.unit if channel else ""
        sample = self.ring_buffer.append(channel_id, value, unit=unit, timestamp_ns=timestamp_ns)

        anomaly: Optional[SensorAnomaly] = None

        if channel:
            # Check upper threshold
            if channel.max_safe_threshold is not None and value > channel.max_safe_threshold:
                anomaly = SensorAnomaly(
                    anomaly_id=f"anom_{len(self.anomalies) + 1:04d}",
                    channel_id=channel_id,
                    anomaly_type="UPPER_THRESHOLD_BREACH",
                    value=value,
                    threshold_limit=channel.max_safe_threshold,
                    timestamp_ns=sample.timestamp_ns,
                    message=f"Channel '{channel.name}' exceeded upper threshold: {value} > {channel.max_safe_threshold} {unit}",
                )

            # Check lower threshold
            elif channel.min_safe_threshold is not None and value < channel.min_safe_threshold:
                anomaly = SensorAnomaly(
                    anomaly_id=f"anom_{len(self.anomalies) + 1:04d}",
                    channel_id=channel_id,
                    anomaly_type="LOWER_THRESHOLD_BREACH",
                    value=value,
                    threshold_limit=channel.min_safe_threshold,
                    timestamp_ns=sample.timestamp_ns,
                    message=f"Channel '{channel.name}' dropped below lower threshold: {value} < {channel.min_safe_threshold} {unit}",
                )

            # Check rate of change spike
            elif channel.max_rate_of_change is not None and channel_id in self.last_values:
                delta = abs(value - self.last_values[channel_id])
                if delta > channel.max_rate_of_change:
                    anomaly = SensorAnomaly(
                        anomaly_id=f"anom_{len(self.anomalies) + 1:04d}",
                        channel_id=channel_id,
                        anomaly_type="RATE_SPIKE",
                        value=value,
                        threshold_limit=channel.max_rate_of_change,
                        timestamp_ns=sample.timestamp_ns,
                        message=f"Rate of change spike on '{channel.name}': delta {delta:.3f} > limit {channel.max_rate_of_change}",
                    )

        if anomaly:
            self.anomalies.append(anomaly)

        self.last_values[channel_id] = value
        return sample, anomaly
