"""
ARES LLM Provider — Abstract Base
All LLM providers must implement this interface.
Changing providers should require only a config change, not code changes.
"""

from abc import ABC, abstractmethod
from typing import Generator


class LLMProvider(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    def generate(self, messages: list[dict]) -> str:
        """Generate a complete response from the given message history.

        Args:
            messages: List of {"role": str, "content": str} dicts.

        Returns:
            The assistant's response text.
        """
        ...

    @abstractmethod
    def generate_stream(self, messages: list[dict]) -> Generator[str, None, None]:
        """Generate a response as a stream of text chunks.

        Args:
            messages: List of {"role": str, "content": str} dicts.

        Yields:
            Text chunks as they arrive from the provider.
        """
        ...

    @abstractmethod
    def supports_images(self) -> bool:
        """Whether this provider can accept image inputs."""
        ...

    @abstractmethod
    def supports_streaming(self) -> bool:
        """Whether this provider supports streaming responses."""
        ...

    @abstractmethod
    def supports_tools(self) -> bool:
        """Whether this provider supports tool/function calling."""
        ...

    def get_info(self) -> dict:
        """Return provider metadata for display purposes."""
        return {
            'name': self.__class__.__name__,
            'images': self.supports_images(),
            'streaming': self.supports_streaming(),
            'tools': self.supports_tools(),
        }
