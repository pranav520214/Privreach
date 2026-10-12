"""
High-Frequency Circular Telemetry Ring Buffer.

Provides constant-time O(1) sample writes and windowed time-range reads
for microsecond-resolution laboratory sensor streams.
"""

from typing import List, Optional, Tuple, Dict, Any
import time
import threading
from pydantic import BaseModel, Field


class TelemetrySample(BaseModel):
    """An individual sensor telemetry measurement."""
    timestamp_ns: int
    channel_id: str
    value: float
    unit: str = ""


class TelemetryRingBuffer:
    """
    Fixed-capacity circular buffer with thread-safe atomic pointer advancement.
    """

    def __init__(self, capacity: int = 50000):
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        self.capacity = capacity
        self.buffer: List[Optional[TelemetrySample]] = [None] * capacity
        self.head: int = 0
        self.size: int = 0
        self.lock = threading.Lock()

    def append(self, channel_id: str, value: float, unit: str = "", timestamp_ns: Optional[int] = None) -> TelemetrySample:
        """
        Appends a new sample to the circular buffer in O(1) time.
        """
        ts = timestamp_ns if timestamp_ns is not None else time.time_ns()
        sample = TelemetrySample(
            timestamp_ns=ts,
            channel_id=channel_id,
            value=float(value),
            unit=unit,
        )

        with self.lock:
            self.buffer[self.head] = sample
            self.head = (self.head + 1) % self.capacity
            if self.size < self.capacity:
                self.size += 1

        return sample

    def read_latest(self, n: int = 10) -> List[TelemetrySample]:
        """
        Retrieves the most recent n samples in chronological order.
        """
        with self.lock:
            if self.size == 0:
                return []
            count = min(n, self.size)
            result = []
            start_idx = (self.head - count) % self.capacity
            for i in range(count):
                idx = (start_idx + i) % self.capacity
                item = self.buffer[idx]
                if item is not None:
                    result.append(item)
            return result

    def read_time_window(self, start_ns: int, end_ns: int, channel_id: Optional[str] = None) -> List[TelemetrySample]:
        """
        Retrieves all samples within [start_ns, end_ns] range, optionally filtered by channel.
        """
        with self.lock:
            if self.size == 0:
                return []
            matched: List[TelemetrySample] = []
            for i in range(self.size):
                idx = (self.head - self.size + i) % self.capacity
                s = self.buffer[idx]
                if s is not None and start_ns <= s.timestamp_ns <= end_ns:
                    if channel_id is None or s.channel_id == channel_id:
                        matched.append(s)
            return matched

    def clear(self) -> None:
        """Resets the ring buffer."""
        with self.lock:
            self.head = 0
            self.size = 0
            self.buffer = [None] * self.capacity
