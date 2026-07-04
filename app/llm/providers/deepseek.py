"""
ARES LLM Provider — DeepSeek
Uses the OpenAI-compatible SDK to communicate with DeepSeek's API.
"""

import logging
from typing import Generator

from openai import OpenAI

from app.llm.base import LLMProvider

logger = logging.getLogger('ares.llm')


class DeepSeekProvider(LLMProvider):
    """DeepSeek API provider via OpenAI-compatible SDK."""

    def __init__(
        self,
        api_key: str,
        model: str = 'deepseek-v4-pro',
        base_url: str = 'https://api.deepseek.com',
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ):
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        if not api_key:
            logger.warning("DeepSeek provider initialized without API key")
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
            logger.info(f"DeepSeek provider initialized — model: {model}")

    def _ensure_client(self):
        if self.client is None:
            raise ConnectionError(
                "No API key configured. Add your DeepSeek API key to config.yaml "
                "or set the ARES_API_KEY environment variable."
            )

    def generate(self, messages: list[dict]) -> str:
        self._ensure_client()
        try:
            logger.debug(f"Generating response ({len(messages)} messages)")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=False,
            )
            content = response.choices[0].message.content or ''
            logger.debug(f"Response received ({len(content)} chars)")
            return content
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise

    def generate_stream(self, messages: list[dict]) -> Generator[str, None, None]:
        self._ensure_client()
        try:
            logger.debug(f"Streaming response ({len(messages)} messages)")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=True,
            )
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            raise

    def supports_images(self) -> bool:
        return True

    def supports_streaming(self) -> bool:
        return True

    def supports_tools(self) -> bool:
        return True

    def get_info(self) -> dict:
        info = super().get_info()
        info['model'] = self.model
        info['provider'] = 'DeepSeek'
        return info
