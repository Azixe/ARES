"""
ARES Orchestrator
Central coordinator. No AI logic — only routing between modules.
"""

import logging
from datetime import datetime
from typing import Generator, Callable

from app.config.settings import Settings
from app.llm.base import LLMProvider
from app.llm.providers.deepseek import DeepSeekProvider
from app.personality.engine import PersonalityEngine
from app.memory.manager import MemoryManager
from app.core.prompt_builder import PromptBuilder
from app.desktop.awareness import DesktopAwareness

logger = logging.getLogger('ares.core')


class Orchestrator:
    """Central coordinator for all ARES modules.

    Receives requests, routes them through the appropriate modules,
    and returns responses. Contains no AI logic — only coordination.
    """

    def __init__(self, settings: Settings):
        self.settings = settings

        # Initialize modules
        self.personality = PersonalityEngine(settings.personality.directory)
        self.memory = MemoryManager(settings.memory.max_conversation_turns)
        self.prompt_builder = PromptBuilder(self.personality)
        self.llm: LLMProvider = self._init_llm()
        self.desktop = DesktopAwareness()

        logger.info("Orchestrator initialized — all modules online")

    def _init_llm(self) -> LLMProvider:
        """Initialize the configured LLM provider."""
        provider = self.settings.llm.provider.lower()

        if provider == 'deepseek':
            return DeepSeekProvider(
                api_key=self.settings.llm.api_key,
                model=self.settings.llm.model,
                base_url=self.settings.llm.base_url,
                max_tokens=self.settings.llm.max_tokens,
                temperature=self.settings.llm.temperature,
            )
        else:
            raise ValueError(
                f"Unknown LLM provider: '{provider}'. "
                f"Available: deepseek"
            )

    def process(self, user_message: str) -> str:
        """Process a user message and return the complete response.

        Args:
            user_message: The user's input text.

        Returns:
            The complete response text.
        """
        logger.info(f"Processing message ({len(user_message)} chars)")

        # Store user message
        self.memory.add_message('user', user_message)

        # Build prompt with desktop context
        desktop_context = self.desktop.format_context()
        messages = self.prompt_builder.build(
            conversation_history=self.memory.get_history(),
            current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            desktop_context=desktop_context,
        )

        # Generate response
        response = self.llm.generate(messages)

        # Store response
        self.memory.add_message('assistant', response)

        logger.info(f"Response generated ({len(response)} chars)")
        return response

    def process_stream(self, user_message: str) -> Generator[str, None, None]:
        """Process a user message and yield response chunks as they arrive.

        Args:
            user_message: The user's input text.

        Yields:
            Text chunks from the LLM provider.
        """
        logger.info(f"Streaming message ({len(user_message)} chars)")

        # Store user message
        self.memory.add_message('user', user_message)

        # Build prompt with desktop context
        desktop_context = self.desktop.format_context()
        messages = self.prompt_builder.build(
            conversation_history=self.memory.get_history(),
            current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            desktop_context=desktop_context,
        )

        # Stream response and collect full text
        full_response = []
        for chunk in self.llm.generate_stream(messages):
            full_response.append(chunk)
            yield chunk

        # Store complete response
        complete = ''.join(full_response)
        self.memory.add_message('assistant', complete)

        logger.info(f"Stream complete ({len(complete)} chars)")

    def get_status(self) -> dict:
        """Return current system status."""
        return {
            'llm_provider': self.settings.llm.provider,
            'llm_model': self.settings.llm.model,
            'conversation_turns': self.memory.get_turn_count(),
            'has_api_key': bool(self.settings.llm.api_key),
            'personality_sections': self.personality.get_section_names(),
        }

    def get_desktop_snapshot(self) -> dict:
        """Return a full desktop awareness snapshot."""
        return self.desktop.get_snapshot()
