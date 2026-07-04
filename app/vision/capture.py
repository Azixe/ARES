"""
ARES Vision — Screenshot Capture Interface Stub
Future: mss + Pillow integration for desktop screenshot analysis.
"""

from abc import ABC, abstractmethod


class VisionCapture(ABC):
    """Abstract interface for screen capture."""

    @abstractmethod
    def capture_screen(self) -> bytes:
        """Capture the full screen as PNG bytes."""
        ...

    @abstractmethod
    def capture_active_window(self) -> bytes:
        """Capture the active window as PNG bytes."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Whether the vision module is ready for use."""
        ...
