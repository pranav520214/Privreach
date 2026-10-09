"""Base Tool Adapter interface for Privreach Tool Graph."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from privearch.schemas import ToolCallResult


class BaseToolAdapter(ABC):
    """
    Abstract base class for all deterministic software adapters.
    Following the principle: 'AI coordinates; specialized software executes.'
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier of the tool adapter."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human and agent readable summary of tool capabilities."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if local binary, library, or interpreter runtime is present."""
        pass

    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> ToolCallResult:
        """
        Execute deterministic processing.
        Returns standardized ToolCallResult.
        """
        pass

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, str]:
        """Default parameter validation hook."""
        return True, ""

