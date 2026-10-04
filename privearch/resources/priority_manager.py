"""Priority Manager: Assigns and adjusts execution priorities across interactive and background workloads."""

from enum import IntEnum
from typing import Dict, Any, Optional


class WorkloadPriority(IntEnum):
    CRITICAL = 1     # User interactive query, immediate UI response
    HIGH = 2         # Interactive mathematical calculation, user-triggered PPT generation
    MEDIUM = 3       # Visualization simulation, report compilation
    LOW = 4          # Video ingestion, audio speech recognition
    BACKGROUND = 5   # Mass embeddings, offline vault rebuild, index cache serialization


class PriorityManager:
    """Manages priority assignments and preemption rules for workloads."""

    DEFAULT_PRIORITIES: Dict[str, WorkloadPriority] = {
        "user_query": WorkloadPriority.CRITICAL,
        "interactive_chat": WorkloadPriority.CRITICAL,
        "interactive_compute": WorkloadPriority.HIGH,
        "ppt_generation": WorkloadPriority.HIGH,
        "pdf_report": WorkloadPriority.HIGH,
        "visualization_rendering": WorkloadPriority.MEDIUM,
        "computational_video": WorkloadPriority.MEDIUM,
        "audio_transcription": WorkloadPriority.LOW,
        "video_indexing": WorkloadPriority.LOW,
        "bm25_indexing": WorkloadPriority.BACKGROUND,
        "embeddings": WorkloadPriority.BACKGROUND,
        "cache_rebuild": WorkloadPriority.BACKGROUND
    }

    @classmethod
    def get_default_priority(cls, workload_type: str, is_interactive: bool = False) -> WorkloadPriority:
        if is_interactive:
            return WorkloadPriority.HIGH
        return cls.DEFAULT_PRIORITIES.get(workload_type, WorkloadPriority.MEDIUM)

    @classmethod
    def is_background_priority(cls, priority: WorkloadPriority) -> bool:
        return priority >= WorkloadPriority.LOW
