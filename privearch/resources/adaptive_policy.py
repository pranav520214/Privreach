"""Adaptive Policy: Controls throttling, concurrency, resolution, and degradation rules."""

from enum import Enum
from typing import Dict, Any, Tuple


class AdaptiveMode(str, Enum):
    ADAPTIVE = "Adaptive"           # Automatic dynamic adjustment based on real-time load
    BALANCED = "Balanced"           # Predictable moderate limits
    PERFORMANCE = "Performance"     # High throughput for dedicated compute runs
    BATTERY_SAVER = "Battery Saver" # Minimal resource footprint to conserve battery & thermals


class AdaptivePolicy:
    """
    Translates real-time system telemetry into concrete operational constraints.
    Enforces the principle: 'Never sacrifice desktop responsiveness for a background task'.
    """

    def __init__(self, mode: AdaptiveMode = AdaptiveMode.ADAPTIVE):
        self.mode = mode

    def set_mode(self, mode: AdaptiveMode) -> None:
        self.mode = mode

    def evaluate(self, telemetry: Dict[str, Any], has_interactive_task: bool = False) -> Dict[str, Any]:
        """
        Calculates operational constraints based on system telemetry and active mode.
        Returns:
            Dict containing worker concurrency, matrix resolution, fps limits,
            sleep throttle delays, and background pause flags.
        """
        cpu_pct = telemetry.get("cpu_percent", 0.0)
        ram_pct = telemetry.get("ram_percent", 0.0)
        on_battery = telemetry.get("on_battery", False)
        stress = telemetry.get("stress_score", 0.0)

        # Baseline defaults
        max_workers = 2
        matrix_res = (100, 100)
        fps = 30
        throttle_sleep = 0.005  # 5ms yield per step
        pause_background = False
        impact_level = "LOW"

        if self.mode == AdaptiveMode.BATTERY_SAVER:
            max_workers = 1
            matrix_res = (50, 50)
            fps = 15
            throttle_sleep = 0.03
            impact_level = "MINIMAL"
            if stress > 0.65 or on_battery:
                pause_background = True

        elif self.mode == AdaptiveMode.PERFORMANCE:
            max_workers = 4
            matrix_res = (120, 120)
            fps = 60
            throttle_sleep = 0.001
            impact_level = "HIGH"
            # In performance mode, only pause if critical memory exhaustion
            if ram_pct > 92.0:
                pause_background = True
                max_workers = 1

        elif self.mode == AdaptiveMode.BALANCED:
            max_workers = 2
            matrix_res = (100, 100)
            fps = 30
            throttle_sleep = 0.008
            impact_level = "MODERATE"
            if stress > 0.80 or ram_pct > 88.0:
                matrix_res = (60, 60)
                fps = 20
                throttle_sleep = 0.02
                max_workers = 1

        else: # AdaptiveMode.ADAPTIVE (Default)
            # Dynamic adjustment according to system pressure & interactive priority
            if has_interactive_task:
                # User is actively chatting, solving, or viewing: throttle background work
                max_workers = 1
                throttle_sleep = 0.025
                impact_level = "INTERACTIVE PRIORITY"
                if stress > 0.70:
                    pause_background = True

            if stress > 0.85 or cpu_pct > 85.0 or ram_pct > 88.0:
                # Heavy system pressure: aggressive degradation
                max_workers = 1
                matrix_res = (40, 40)
                fps = 15
                throttle_sleep = 0.04
                pause_background = True
                impact_level = "THROTTLED (HEAVY LOAD)"

            elif stress > 0.65 or cpu_pct > 65.0:
                # Moderate load: degrade visual matrix and frame rate first
                max_workers = 1
                matrix_res = (75, 75)
                fps = 20
                throttle_sleep = 0.015
                impact_level = "ADAPTED (MEDIUM LOAD)"

            else:
                # System is calm and responsive: run standard 100x100 matrix at 30 fps
                max_workers = 3
                matrix_res = (100, 100)
                fps = 30
                throttle_sleep = 0.003
                impact_level = "OPTIMAL"

        return {
            "mode": self.mode.value,
            "max_workers": max_workers,
            "matrix_resolution": matrix_res,
            "fps_limit": fps,
            "throttle_sleep_s": throttle_sleep,
            "pause_background": pause_background,
            "impact_level": impact_level,
            "stress_score": stress
        }
