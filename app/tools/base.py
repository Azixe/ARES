"""
ARES Tools — Tool Interface Stub
Future: Filesystem, Calculator, Clipboard, Time, Weather, etc.
"""

from abc import ABC, abstractmethod
from typing import Any


class Tool(ABC):
    """Abstract interface for ARES tools."""

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """Execute the tool with given parameters."""
        ...

    @abstractmethod
    def describe(self) -> str:
        """Return a human-readable description of what this tool does."""
        ...

    @abstractmethod
    def permissions(self) -> list[str]:
        """Return required permissions (e.g., 'filesystem.read', 'network')."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool identifier."""
        ...
