"""
ARES Configuration System
Loads .env for secrets, then config.yaml, with environment variable overrides.
Priority: env vars > .env > config.yaml > defaults
"""

import os
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv

logger = logging.getLogger('ares.config')


@dataclass
class LLMConfig:
    provider: str = 'deepseek'
    model: str = 'deepseek-v4-pro'
    api_key: str = ''
    base_url: str = 'https://api.deepseek.com'
    max_tokens: int = 32000
    temperature: float = 0.7
    streaming: bool = True


@dataclass
class PersonalityConfig:
    directory: str = 'app/personality'


@dataclass
class MemoryConfig:
    max_conversation_turns: int = 20


@dataclass
class VisionConfig:
    enabled: bool = False


@dataclass
class VoiceConfig:
    tts_enabled: bool = False
    stt_enabled: bool = False


@dataclass
class UIConfig:
    theme: str = 'dark'
    title: str = 'ARES'
    width: int = 900
    height: int = 700


@dataclass
class LoggingConfig:
    level: str = 'INFO'
    directory: str = 'logs'


def _merge_dataclass(instance, data: dict):
    """Merge a dict into a dataclass, only updating fields that exist."""
    if not data:
        return instance
    valid_fields = {f.name for f in instance.__dataclass_fields__.values()}
    for key, value in data.items():
        if key in valid_fields and value is not None:
            setattr(instance, key, value)
    return instance


@dataclass
class Settings:
    llm: LLMConfig = field(default_factory=LLMConfig)
    personality: PersonalityConfig = field(default_factory=PersonalityConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    vision: VisionConfig = field(default_factory=VisionConfig)
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    _project_root: Optional[Path] = field(default=None, repr=False)

    @classmethod
    def load(cls, config_path: str = 'config.yaml') -> 'Settings':
        """Load settings from .env + YAML with environment variable overrides."""
        settings = cls()

        # Determine project root from config file location
        config_file = Path(config_path).resolve()
        if config_file.exists():
            settings._project_root = config_file.parent
        else:
            settings._project_root = Path.cwd()

        # Load .env file (secrets go here, not in config.yaml)
        env_file = settings._project_root / '.env'
        if env_file.exists():
            load_dotenv(env_file)
            logger.info("Loaded environment from .env")
        else:
            logger.debug(".env file not found — using system environment only")

        # Load YAML
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {}

                _merge_dataclass(settings.llm, data.get('llm'))
                _merge_dataclass(settings.personality, data.get('personality'))
                _merge_dataclass(settings.memory, data.get('memory'))
                _merge_dataclass(settings.vision, data.get('vision'))
                _merge_dataclass(settings.voice, data.get('voice'))
                _merge_dataclass(settings.ui, data.get('ui'))
                _merge_dataclass(settings.logging, data.get('logging'))

                logger.info(f"Configuration loaded from {config_file}")
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
        else:
            logger.warning(f"Config file not found: {config_file}. Using defaults.")

        # Environment variable overrides
        env_key = os.environ.get('ARES_API_KEY', '').strip()
        if env_key:
            settings.llm.api_key = env_key
            logger.info("API key loaded from ARES_API_KEY environment variable")

        env_provider = os.environ.get('ARES_LLM_PROVIDER', '').strip()
        if env_provider:
            settings.llm.provider = env_provider

        env_model = os.environ.get('ARES_LLM_MODEL', '').strip()
        if env_model:
            settings.llm.model = env_model

        # Resolve personality directory relative to project root
        personality_dir = Path(settings.personality.directory)
        if not personality_dir.is_absolute():
            settings.personality.directory = str(
                settings._project_root / personality_dir
            )

        # Validate
        if not settings.llm.api_key:
            logger.warning(
                "No API key configured. "
                "Set ARES_API_KEY in .env or as an environment variable."
            )

        return settings

    @property
    def project_root(self) -> Path:
        return self._project_root or Path.cwd()
