"""
ARES Memory Manager
Phase 1: In-memory conversation history with sliding window.
Future: RAG integration with ChromaDB.
"""

import threading
import logging

logger = logging.getLogger('ares.memory')


class MemoryManager:
    """Manages conversation history with a sliding window.

    Thread-safe for concurrent access from UI and orchestrator threads.
    """

    def __init__(self, max_turns: int = 20):
        self.max_turns = max_turns
        self._history: list[dict] = []
        self._lock = threading.Lock()
        logger.info(f"Memory manager initialized — max {max_turns} turns")

    def add_message(self, role: str, content: str):
        """Add a message to conversation history.

        Args:
            role: 'user' or 'assistant'
            content: Message text
        """
        with self._lock:
            self._history.append({'role': role, 'content': content})

            # Trim to max capacity (each turn = user + assistant = 2 messages)
            max_messages = self.max_turns * 2
            if len(self._history) > max_messages:
                overflow = len(self._history) - max_messages
                self._history = self._history[overflow:]
                logger.debug(f"History trimmed: removed {overflow} oldest messages")

    def get_history(self) -> list[dict]:
        """Return a copy of the current conversation history."""
        with self._lock:
            return list(self._history)

    def clear(self):
        """Clear all conversation history."""
        with self._lock:
            count = len(self._history)
            self._history.clear()
            logger.info(f"Conversation history cleared ({count} messages removed)")

    def get_turn_count(self) -> int:
        """Return approximate number of conversation turns."""
        with self._lock:
            return len(self._history) // 2

    def get_message_count(self) -> int:
        """Return total number of messages in history."""
        with self._lock:
            return len(self._history)
