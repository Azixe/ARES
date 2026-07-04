"""
ARES Personality Engine
Loads personality definition files and compiles them into a system prompt.
"""

import logging
from pathlib import Path

logger = logging.getLogger('ares.personality')


class PersonalityEngine:
    """Loads and compiles personality markdown files into a system prompt."""

    def __init__(self, personality_dir: str):
        self.directory = Path(personality_dir)
        self._compiled: str | None = None

        # Ordered loading — sequence matters for prompt structure
        self._file_order = [
            'communication.md',
            'behavior.md',
            'reasoning.md',
            'ethics.md',
        ]

        if not self.directory.exists():
            logger.warning(f"Personality directory not found: {self.directory}")
        else:
            logger.info(f"Personality engine loaded from: {self.directory}")

    def compile(self) -> str:
        """Compile all personality files into a single system prompt.

        Returns cached version if available. Call refresh() to force reload.
        """
        if self._compiled is not None:
            return self._compiled

        sections = []

        for filename in self._file_order:
            filepath = self.directory / filename
            if filepath.exists():
                try:
                    content = filepath.read_text(encoding='utf-8').strip()
                    if content:
                        sections.append(content)
                        logger.debug(f"Loaded personality file: {filename}")
                except Exception as e:
                    logger.error(f"Failed to read {filename}: {e}")
            else:
                logger.warning(f"Personality file missing: {filename}")

        # Also load any additional .md files not in the default order
        if self.directory.exists():
            for md_file in sorted(self.directory.glob('*.md')):
                if md_file.name not in self._file_order:
                    try:
                        content = md_file.read_text(encoding='utf-8').strip()
                        if content:
                            sections.append(content)
                            logger.debug(f"Loaded extra personality file: {md_file.name}")
                    except Exception as e:
                        logger.error(f"Failed to read {md_file.name}: {e}")

        self._compiled = '\n\n---\n\n'.join(sections)
        logger.info(
            f"Personality compiled: {len(sections)} sections, "
            f"{len(self._compiled)} characters"
        )
        return self._compiled

    def refresh(self):
        """Force recompilation on next compile() call."""
        self._compiled = None
        logger.info("Personality cache cleared — will recompile on next request")

    def get_section_names(self) -> list[str]:
        """Return list of loaded personality file names."""
        if not self.directory.exists():
            return []
        return [f.name for f in self.directory.glob('*.md')]
