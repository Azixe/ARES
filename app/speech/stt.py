"""
ARES Speech — STT Interface Stub
Future: faster-whisper integration for voice input.
"""

from abc import ABC, abstractmethod


class STTEngine(ABC):
    """Abstract interface for speech-to-text engines."""

    @abstractmethod
    def transcribe(self, audio: bytes) -> str:
        """Transcribe audio bytes to text."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Whether the STT engine is ready for use."""
        ...

    @abstractmethod
    def is_listening(self) -> bool:
        """Whether the engine is currently recording/transcribing."""
        ...
