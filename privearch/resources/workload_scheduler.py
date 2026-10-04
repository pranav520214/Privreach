"""Workload Scheduler: Cooperative scheduling, progress tracking, pause/resume, and cancellation."""

import time
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from enum import Enum
from typing import Dict, Any, List, Optional, Callable

from privearch.resources.priority_manager import WorkloadPriority


class WorkloadStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class WorkloadCancelledException(Exception):
    """Raised when a cooperative workload is cancelled by user or scheduler."""
    pass


class Workload:
    """Represents a scheduled, tracked, and interruptible unit of computation."""

    def __init__(
        self,
        name: str,
        workload_type: str,
        fn: Callable[['Workload'], Any],
        priority: WorkloadPriority = WorkloadPriority.MEDIUM,
        is_interactive: bool = False,
        estimated_resources: Optional[Dict[str, Any]] = None
    ):
        self.workload_id = f"job_{uuid.uuid4().hex[:8]}"
        self.name = name
        self.workload_type = workload_type
        self.fn = fn
        self.priority = priority
        self.is_interactive = is_interactive
        self.estimated_resources = estimated_resources or {"cpu": "medium", "ram": "low"}

        self.status = WorkloadStatus.QUEUED
        self.progress = 0.0
        self.status_message = "Queued for execution."
        self.start_time = 0.0
        self.end_time = 0.0
        self.result: Any = None
        self.error: Optional[str] = None

        self._pause_event = threading.Event()
        self._pause_event.set()  # set = running, clear = paused
        self._cancel_event = threading.Event()

    def update_progress(self, progress: float, message: str = "") -> None:
        """Update job completion percentage (0.0 to 100.0) and status string."""
        self.progress = max(0.0, min(100.0, round(progress, 1)))
        if message:
            self.status_message = message

    def is_cancelled(self) -> bool:
        return self._cancel_event.is_set()

    def is_paused(self) -> bool:
        return not self._pause_event.is_set()

    def pause(self) -> None:
        """Pauses workload execution at the next cooperative yield point."""
        if self.status == WorkloadStatus.RUNNING:
            self.status = WorkloadStatus.PAUSED
            self.status_message = "Paused by resource manager."
            self._pause_event.clear()

    def resume(self) -> None:
        """Resumes a paused workload."""
        if self.status == WorkloadStatus.PAUSED:
            self.status = WorkloadStatus.RUNNING
            self.status_message = "Resumed execution."
            self._pause_event.set()

    def cancel(self) -> None:
        """Signals cancellation to the workload."""
        self.status = WorkloadStatus.CANCELLED
        self.status_message = "Cancelled by user."
        self._cancel_event.set()
        self._pause_event.set()  # Unblock if currently waiting in pause

    def check_cooperative(self, throttle_delay_s: float = 0.0) -> None:
        """
        Cooperative yield point:
        1. Checks cancellation.
        2. Waits if paused.
        3. Sleeps throttle_delay_s to yield CPU time slices to active desktop applications.
        """
        if self.is_cancelled():
            raise WorkloadCancelledException(f"Workload {self.name} was cancelled.")

        # If paused, wait until resumed or cancelled
        while not self._pause_event.is_set():
            if self.is_cancelled():
                raise WorkloadCancelledException(f"Workload {self.name} was cancelled while paused.")
            time.sleep(0.1)

        # Non-disruptive throttle sleep
        if throttle_delay_s > 0.0:
            time.sleep(throttle_delay_s)


class WorkloadScheduler:
    """Manages thread pool and priority lifecycle of workloads."""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="PrivreachWorker")
        self._workloads: Dict[str, Workload] = {}
        self._futures: Dict[str, Future] = {}
        self._lock = threading.Lock()

    def submit(
        self,
        name: str,
        workload_type: str,
        fn: Callable[[Workload], Any],
        priority: WorkloadPriority = WorkloadPriority.MEDIUM,
        is_interactive: bool = False,
        estimated_resources: Optional[Dict[str, Any]] = None
    ) -> Workload:
        """Submits a workload for background execution."""
        workload = Workload(
            name=name,
            workload_type=workload_type,
            fn=fn,
            priority=priority,
            is_interactive=is_interactive,
            estimated_resources=estimated_resources
        )

        with self._lock:
            self._workloads[workload.workload_id] = workload

        def _run_wrapper(w: Workload):
            w.status = WorkloadStatus.RUNNING
            w.start_time = time.time()
            try:
                w.result = w.fn(w)
                if w.status != WorkloadStatus.CANCELLED:
                    w.status = WorkloadStatus.COMPLETED
                    w.progress = 100.0
                    w.status_message = "Completed successfully."
            except WorkloadCancelledException:
                w.status = WorkloadStatus.CANCELLED
                w.status_message = "Execution cancelled."
            except Exception as e:
                w.status = WorkloadStatus.FAILED
                w.error = str(e)
                w.status_message = f"Failed: {e}"
            finally:
                w.end_time = time.time()

        future = self._executor.submit(_run_wrapper, workload)
        with self._lock:
            self._futures[workload.workload_id] = future

        return workload

    def execute_sync(
        self,
        name: str,
        workload_type: str,
        fn: Callable[[Workload], Any],
        priority: WorkloadPriority = WorkloadPriority.HIGH,
        is_interactive: bool = True
    ) -> Any:
        """Executes a workload synchronously while tracking progress and cooperative cancellation."""
        workload = Workload(
            name=name,
            workload_type=workload_type,
            fn=fn,
            priority=priority,
            is_interactive=is_interactive
        )
        with self._lock:
            self._workloads[workload.workload_id] = workload

        workload.status = WorkloadStatus.RUNNING
        workload.start_time = time.time()
        try:
            workload.result = workload.fn(workload)
            if workload.status != WorkloadStatus.CANCELLED:
                workload.status = WorkloadStatus.COMPLETED
                workload.progress = 100.0
                workload.status_message = "Completed."
            return workload.result
        except WorkloadCancelledException:
            workload.status = WorkloadStatus.CANCELLED
            workload.status_message = "Execution cancelled."
            raise
        except Exception as e:
            workload.status = WorkloadStatus.FAILED
            workload.error = str(e)
            workload.status_message = f"Failed: {e}"
            raise
        finally:
            workload.end_time = time.time()

    def get(self, workload_id: str) -> Optional[Workload]:
        with self._lock:
            return self._workloads.get(workload_id)

    def pause(self, workload_id: str) -> bool:
        w = self.get(workload_id)
        if w:
            w.pause()
            return True
        return False

    def resume(self, workload_id: str) -> bool:
        w = self.get(workload_id)
        if w:
            w.resume()
            return True
        return False

    def cancel(self, workload_id: str) -> bool:
        w = self.get(workload_id)
        if w:
            w.cancel()
            return True
        return False

    def pause_all_background(self) -> int:
        count = 0
        with self._lock:
            for w in self._workloads.values():
                if not w.is_interactive and w.status == WorkloadStatus.RUNNING:
                    w.pause()
                    count += 1
        return count

    def resume_all_background(self) -> int:
        count = 0
        with self._lock:
            for w in self._workloads.values():
                if not w.is_interactive and w.status == WorkloadStatus.PAUSED:
                    w.resume()
                    count += 1
        return count

    def cancel_all(self) -> int:
        count = 0
        with self._lock:
            for w in self._workloads.values():
                if w.status in (WorkloadStatus.RUNNING, WorkloadStatus.QUEUED, WorkloadStatus.PAUSED):
                    w.cancel()
                    count += 1
        return count

    def get_all(self) -> List[Workload]:
        with self._lock:
            return list(self._workloads.values())

    def get_active(self) -> List[Workload]:
        with self._lock:
            return [w for w in self._workloads.values() if w.status in (WorkloadStatus.RUNNING, WorkloadStatus.PAUSED)]
