"""
Unit and Integration Tests for privreach.lab telemetry and experiment stream.
"""

import unittest
import time

from privreach.lab.ring_buffer import TelemetryRingBuffer
from privreach.lab.sensor_ingest import SensorIngestEngine
from privreach.lab.ocr_reader import InstrumentOCRReader
from privreach.lab.temporal_correlator import TemporalCorrelator


class TestLabSubsystem(unittest.TestCase):
    """Verifies telemetry ring buffer, multi-channel sensor ingestion, OCR, and temporal correlation."""

    def setUp(self):
        self.ring_buffer = TelemetryRingBuffer(capacity=100)
        self.sensor_engine = SensorIngestEngine(self.ring_buffer)
        self.ocr_reader = InstrumentOCRReader()
        self.correlator = TemporalCorrelator(self.ring_buffer)

    def test_ring_buffer_append_and_wraparound(self):
        """Buffer advances circularly and preserves most recent elements past capacity."""
        buf = TelemetryRingBuffer(capacity=5)
        for i in range(10):
            buf.append(channel_id="temp", value=float(i), unit="C", timestamp_ns=1000 + i)

        self.assertEqual(buf.size, 5)
        latest = buf.read_latest(5)
        self.assertEqual(len(latest), 5)
        # Should contain values 5, 6, 7, 8, 9
        values = [s.value for s in latest]
        self.assertEqual(values, [5.0, 6.0, 7.0, 8.0, 9.0])

    def test_ring_buffer_time_window_filtering(self):
        """Reads exact time range slices."""
        buf = TelemetryRingBuffer(capacity=50)
        buf.append("temp", 20.0, timestamp_ns=100)
        buf.append("temp", 25.0, timestamp_ns=200)
        buf.append("temp", 30.0, timestamp_ns=300)
        buf.append("temp", 35.0, timestamp_ns=400)

        window = buf.read_time_window(start_ns=150, end_ns=350)
        self.assertEqual(len(window), 2)
        self.assertEqual([s.value for s in window], [25.0, 30.0])

    def test_sensor_ingest_threshold_breach(self):
        """Triggers deterministic anomaly upon safety threshold violation."""
        self.sensor_engine.register_channel(
            channel_id="reactor_temp",
            name="Chemical Reactor Temperature",
            unit="degC",
            max_safe=150.0,
            max_rate_of_change=25.0,
        )

        # Normal reading
        sample1, anom1 = self.sensor_engine.ingest_reading("reactor_temp", 120.0)
        self.assertIsNone(anom1)

        # Breach reading (> 150.0)
        sample2, anom2 = self.sensor_engine.ingest_reading("reactor_temp", 165.0)
        self.assertIsNotNone(anom2)
        self.assertEqual(anom2.anomaly_type, "UPPER_THRESHOLD_BREACH")
        self.assertEqual(anom2.value, 165.0)
        self.assertEqual(anom2.threshold_limit, 150.0)

    def test_instrument_ocr_gauge_parsing(self):
        """Extracts numeric readings and unit descriptors from digital display OCR output."""
        res_temp = self.ocr_reader.parse_display_text("TEMP: 84.5 °C STABLE", device_label="heater_01")
        self.assertIsNotNone(res_temp)
        self.assertEqual(res_temp.value, 84.5)
        self.assertEqual(res_temp.unit, "degC")

        res_press = self.ocr_reader.parse_display_text("CHAMBER 1.025 bar OK", device_label="gauge_02")
        self.assertIsNotNone(res_press)
        self.assertEqual(res_press.value, 1.025)
        self.assertEqual(res_press.unit, "bar")

    def test_temporal_correlator_snapshots_ambient_state(self):
        """Event captures surrounding ambient sensor telemetry at that exact nanosecond."""
        # Simulate background sensor telemetry
        t0 = time.time_ns()
        self.ring_buffer.append("temp_ch", 82.5, unit="degC", timestamp_ns=t0 - 100_000)
        self.ring_buffer.append("pressure_ch", 1.03, unit="bar", timestamp_ns=t0 - 50_000)

        # Action event occurs at t0
        event = self.correlator.record_event(
            event_type="VISION_ACTION",
            description="Researcher injected titanium catalyst into flask A",
            timestamp_ns=t0,
        )

        self.assertIn("temp_ch", event.sensor_snapshot)
        self.assertIn("pressure_ch", event.sensor_snapshot)
        self.assertEqual(event.sensor_snapshot["temp_ch"], 82.5)
        self.assertEqual(event.sensor_snapshot["pressure_ch"], 1.03)

        # Query events
        results = self.correlator.query_events("catalyst")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].event_id, event.event_id)


if __name__ == "__main__":
    unittest.main()
