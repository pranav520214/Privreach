"""Central Adaptive Resource Manager for Privreach."""

import time
import threading
from typing import Dict, Any, List, Optional, Callable

from privearch.resources.system_monitor import SystemMonitor
from privearch.resources.adaptive_policy import AdaptivePolicy, AdaptiveMode
from privearch.resources.priority_manager import PriorityManager, WorkloadPriority
from privearch.resources.workload_scheduler import WorkloadScheduler, Workload, WorkloadStatus


class ResourceManager:
    """
    Central Resource Manager / Scheduler responsible for all background
    and compute-heavy Privreach workloads (CPU, GPU, RAM, VRAM, I/O, priorities).
    Enforces adaptive, non-disruptive desktop execution.
    """

    def __init__(self, mode: AdaptiveMode = AdaptiveMode.ADAPTIVE):
        self.monitor = SystemMonitor()
        self.policy = AdaptivePolicy(mode=mode)
        self.priority_manager = PriorityManager()
        self.scheduler = WorkloadScheduler(max_workers=4)

        self._active_telemetry = self.monitor.get_telemetry()
        self._current_constraints = self.policy.evaluate(self._active_telemetry)

        self._running = True
        self._monitor_thread = threading.Thread(target=self._telemetry_daemon, daemon=True, name="PrivreachResourceDaemon")
        self._monitor_thread.start()

    def set_mode(self, mode: AdaptiveMode) -> None:
        """Switch adaptive behavior mode."""
        self.policy.set_mode(mode)
        self._update_constraints()

    def _update_constraints(self) -> None:
        """Recalculate adaptive constraints based on active telemetry."""
        has_interactive = any(w.is_interactive for w in self.get_active_workloads())
        self._current_constraints = self.policy.evaluate(self._active_telemetry, has_interactive_task=has_interactive)

    def get_mode(self) -> AdaptiveMode:
        return self.policy.mode

    def get_telemetry(self) -> Dict[str, Any]:
        return dict(self._active_telemetry)

    def get_constraints(self) -> Dict[str, Any]:
        return dict(self._current_constraints)

    def submit_workload(
        self,
        name: str,
        workload_type: str,
        fn: Callable[[Workload], Any],
        priority: Optional[WorkloadPriority] = None,
        is_interactive: bool = False,
        estimated_resources: Optional[Dict[str, Any]] = None
    ) -> Workload:
        """Registers and schedules a new workload under adaptive management."""
        eff_priority = priority or self.priority_manager.get_default_priority(workload_type, is_interactive)
        return self.scheduler.submit(
            name=name,
            workload_type=workload_type,
            fn=fn,
            priority=eff_priority,
            is_interactive=is_interactive,
            estimated_resources=estimated_resources
        )

    def execute_sync(
        self,
        name: str,
        workload_type: str,
        fn: Callable[[Workload], Any],
        priority: Optional[WorkloadPriority] = None,
        is_interactive: bool = True
    ) -> Any:
        """Executes an interactive workload synchronously while reporting progress and obeying resource limits."""
        eff_priority = priority or self.priority_manager.get_default_priority(workload_type, is_interactive)
        return self.scheduler.execute_sync(
            name=name,
            workload_type=workload_type,
            fn=fn,
            priority=eff_priority,
            is_interactive=is_interactive
        )

    def pause_workload(self, workload_id: str) -> bool:
        return self.scheduler.pause(workload_id)

    def resume_workload(self, workload_id: str) -> bool:
        return self.scheduler.resume(workload_id)

    def cancel_workload(self, workload_id: str) -> bool:
        return self.scheduler.cancel(workload_id)

    def pause_all_background(self) -> int:
        return self.scheduler.pause_all_background()

    def resume_all_background(self) -> int:
        return self.scheduler.resume_all_background()

    def cancel_all(self) -> int:
        return self.scheduler.cancel_all()

    def get_active_workloads(self) -> List[Workload]:
        return self.scheduler.get_active()

    def format_console_status(self, current_model: str = "qwen2.5-coder:3b") -> str:
        """
        Formats real-time terminal status output for the Execution Console.
        """
        t = self._active_telemetry
        c = self._current_constraints
        mode_str = self.policy.mode.value.upper()

        lines = [
            f"PRIVREACH ENGINE [Mode: {mode_str}] [Impact: {c.get('impact_level', 'LOW')}]",
            f"CPU: {t['cpu_percent']:.1f}% | RAM: {t['ram_percent']:.1f}% ({t['ram_available_gb']} GB free) | GPU: {t['gpu_percent']:.1f}% | VRAM: {t['vram_used_gb']} GB",
            f"Active Model: {current_model} | Concurrency: {c['max_workers']} workers | FPS: {c['fps_limit']}",
            "----------------------------------------------------------------------"
        ]

        active_jobs = self.get_active_workloads()
        if active_jobs:
            for job in active_jobs[:3]:
                status_icon = "▶" if job.status == WorkloadStatus.RUNNING else "⏸"
                lines.append(f"{status_icon} {job.name:<24} [{job.progress:>5.1f}%] - {job.status_message}")
        else:
            lines.append("✓ Background workers idle. Zero desktop contention.")

        # Summary tracker
        all_jobs = self.scheduler.get_all()
        by_type: Dict[str, List[Workload]] = {}
        for j in all_jobs:
            by_type.setdefault(j.workload_type, []).append(j)

        type_summaries = []
        for t_name, jobs in by_type.items():
            latest = jobs[-1]
            type_summaries.append(f"{t_name:<20} .. {latest.status.value} ({latest.progress:.0f}%)")

        if type_summaries:
            lines.append("----------------------------------------------------------------------")
            lines.extend(type_summaries[-4:])

        return "\n".join(lines)

    def _telemetry_daemon(self) -> None:
        """Background thread updating telemetry and auto-adapting constraints every 1.5s."""
        while self._running:
            try:
                self._active_telemetry = self.monitor.get_telemetry()
                has_interactive = any(w.is_interactive for w in self.get_active_workloads())
                self._current_constraints = self.policy.evaluate(self._active_telemetry, has_interactive_task=has_interactive)

                # Automatic throttling in ADAPTIVE mode
                if self.policy.mode == AdaptiveMode.ADAPTIVE and self._current_constraints.get("pause_background"):
                    self.scheduler.pause_all_background()
                elif self.policy.mode == AdaptiveMode.ADAPTIVE and not self._current_constraints.get("pause_background"):
                    # Unpause jobs paused by auto-throttling
                    for w in self.scheduler.get_all():
                        if w.status == WorkloadStatus.PAUSED and "resource manager" in w.status_message.lower():
                            w.resume()

            except Exception:
                pass
            time.sleep(1.5)

    def shutdown(self) -> None:
        self._running = False
        self.scheduler.cancel_all()
