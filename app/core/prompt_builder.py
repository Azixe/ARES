"""
ARES Prompt Builder
Assembles the full message list for LLM calls.
Order: System (personality + time + context) → History → User message.
"""

import logging
from datetime import datetime

from app.personality.engine import PersonalityEngine

logger = logging.getLogger('ares.core')


class PromptBuilder:
    """Assembles structured prompts for LLM consumption."""

    def __init__(self, personality: PersonalityEngine):
        self.personality = personality

    def build(
        self,
        conversation_history: list[dict],
        current_time: str | None = None,
        memories: list[str] | None = None,
        screenshot_description: str | None = None,
    ) -> list[dict]:
        """Build the complete message list for an LLM call.

        Args:
            conversation_history: List of {"role": str, "content": str} dicts.
                Should already include the latest user message.
            current_time: ISO timestamp string.
            memories: Retrieved RAG context strings.
            screenshot_description: Description of a captured screenshot.

        Returns:
            Complete message list ready for LLM provider.
        """
        messages = []

        # === SYSTEM PROMPT ===
        system_parts = []

        # Personality
        personality_text = self.personality.compile()
        if personality_text:
            system_parts.append(personality_text)

        # Current time
        if current_time:
            system_parts.append(f"## Current Time\n{current_time}")

        # Retrieved memories (RAG context)
        if memories:
            context = '\n'.join(f'- {m}' for m in memories)
            system_parts.append(f"## Relevant Context\n{context}")

        # Screenshot context
        if screenshot_description:
            system_parts.append(
                f"## Visual Context\n"
                f"A screenshot has been captured. Description:\n{screenshot_description}"
            )

        system_prompt = '\n\n---\n\n'.join(system_parts)
        messages.append({'role': 'system', 'content': system_prompt})

        # === CONVERSATION HISTORY ===
        # History already contains all messages including the latest user message
        for msg in conversation_history:
            messages.append({'role': msg['role'], 'content': msg['content']})

        logger.debug(
            f"Prompt built: {len(messages)} messages, "
            f"system prompt {len(system_prompt)} chars"
        )
        return messages
