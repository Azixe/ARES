"""
ARES Voice — TTS Interface Stub
Future: Piper TTS integration for Super Tactical Droid-style voice.
"""

from abc import ABC, abstractmethod


class TTSEngine(ABC):
    """Abstract interface for text-to-speech engines."""

    @abstractmethod
    def synthesize(self, text: str) -> bytes:
        """Convert text to audio bytes (WAV format)."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Whether the TTS engine is ready for use."""
        ...

    @abstractmethod
    def get_voice_info(self) -> dict:
        """Return metadata about the current voice configuration."""
        ...
