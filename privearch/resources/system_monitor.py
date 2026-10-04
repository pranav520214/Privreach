"""System Monitor: Telemetry collector for CPU, GPU, RAM, VRAM, disk, battery, and temperatures."""

import os
import time
import shutil
import subprocess
from typing import Dict, Any, Optional
import psutil


class SystemMonitor:
    """
    Monitors host system resources with negligible overhead (<0.1% CPU).
    Provides real-time telemetry to the Adaptive Policy.
    """

    def __init__(self):
        self._proc = psutil.Process(os.getpid())
        self._last_disk_io = psutil.disk_io_counters()
        self._last_disk_time = time.time()
        self._nvidia_smi_available = shutil.which("nvidia-smi") is not None
        self._cached_gpu_telemetry: Dict[str, Any] = {"gpu_util_percent": 0.0, "vram_used_gb": 0.0, "vram_total_gb": 4.0, "available": False}
        self._last_gpu_query_time = 0.0

    def get_telemetry(self) -> Dict[str, Any]:
        """Collects instantaneous snapshot of system performance metrics."""
        # CPU
        cpu_percent = psutil.cpu_percent(interval=None)
        proc_cpu = 0.0
        try:
            proc_cpu = self._proc.cpu_percent(interval=None)
        except Exception:
            pass

        # RAM
        vm = psutil.virtual_memory()
        ram_percent = vm.percent
        ram_available_gb = round(vm.available / (1024 ** 3), 2)
        ram_total_gb = round(vm.total / (1024 ** 3), 2)
        proc_ram_mb = round(self._proc.memory_info().rss / (1024 ** 2), 1)

        # Battery / Power
        battery_saver_active = False
        on_battery = False
        battery_percent = 100
        try:
            battery = psutil.sensors_battery()
            if battery is not None:
                on_battery = not battery.power_plugged
                battery_percent = int(battery.percent)
                if on_battery and battery_percent < 35:
                    battery_saver_active = True
        except Exception:
            pass

        # Disk I/O
        disk_rate_mb = 0.0
        try:
            curr_io = psutil.disk_io_counters()
            now = time.time()
            dt = now - self._last_disk_time
            if curr_io and self._last_disk_io and dt > 0.5:
                bytes_delta = (curr_io.read_bytes + curr_io.write_bytes) - (self._last_disk_io.read_bytes + self._last_disk_io.write_bytes)
                disk_rate_mb = round(bytes_delta / (1024 * 1024 * dt), 2)
                self._last_disk_io = curr_io
                self._last_disk_time = now
        except Exception:
            pass

        # GPU / VRAM (Rate limited to 1 query every 3 seconds to avoid subprocess overhead)
        gpu_info = self._get_gpu_telemetry()

        # Temperature
        temp_c = self._get_system_temperature()

        # Compute composite system load score (0.0 to 1.0)
        # Higher score means system is under heavy strain
        stress_score = (
            (cpu_percent / 100.0) * 0.45 +
            (ram_percent / 100.0) * 0.35 +
            (gpu_info["gpu_util_percent"] / 100.0) * 0.20
        )
        if on_battery and battery_percent < 25:
            stress_score = max(stress_score, 0.85)

        return {
            "cpu_percent": cpu_percent,
            "proc_cpu_percent": proc_cpu,
            "ram_percent": ram_percent,
            "ram_available_gb": ram_available_gb,
            "ram_total_gb": ram_total_gb,
            "proc_ram_mb": proc_ram_mb,
            "gpu_percent": gpu_info["gpu_util_percent"],
            "vram_used_gb": gpu_info["vram_used_gb"],
            "vram_total_gb": gpu_info["vram_total_gb"],
            "has_discrete_gpu": gpu_info["available"],
            "on_battery": on_battery,
            "battery_percent": battery_percent,
            "disk_io_mb_s": disk_rate_mb,
            "temperature_c": temp_c,
            "stress_score": round(stress_score, 3),
            "timestamp": time.time()
        }

    def _get_gpu_telemetry(self) -> Dict[str, Any]:
        """Queries GPU status with low latency caching."""
        now = time.time()
        if now - self._last_gpu_query_time < 3.0:
            return self._cached_gpu_telemetry

        self._last_gpu_query_time = now
        if not self._nvidia_smi_available:
            return self._cached_gpu_telemetry

        try:
            res = subprocess.run(
                ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=0.6,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
            )
            if res.returncode == 0 and res.stdout.strip():
                parts = [p.strip() for p in res.stdout.strip().split(",")]
                if len(parts) >= 3:
                    util = float(parts[0])
                    used_mb = float(parts[1])
                    total_mb = float(parts[2])
                    self._cached_gpu_telemetry = {
                        "gpu_util_percent": util,
                        "vram_used_gb": round(used_mb / 1024, 2),
                        "vram_total_gb": round(total_mb / 1024, 2),
                        "available": True
                    }
        except Exception:
            pass

        return self._cached_gpu_telemetry

    def _get_system_temperature(self) -> Optional[float]:
        """Attempts to read platform hardware temperatures if supported."""
        try:
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if temps:
                    for name, entries in temps.items():
                        for entry in entries:
                            if entry.current is not None:
                                return float(entry.current)
        except Exception:
            pass
        return None
