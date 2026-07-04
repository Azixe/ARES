"""
ARES — Adaptive Reasoning Executive System
Entry Point

Launch with: python main.py
"""

import sys
import logging
from pathlib import Path

# Ensure project root is in Python path
PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from app.config.settings import Settings
from app.core.orchestrator import Orchestrator
from app.ui.api import AresAPI
from app.ui.window import create_window, start


def setup_logging(settings: Settings):
    """Configure the logging system with console and file handlers."""
    log_dir = PROJECT_ROOT / settings.logging.directory
    log_dir.mkdir(exist_ok=True)

    level = getattr(logging, settings.logging.level.upper(), logging.INFO)

    # Root ARES logger
    root_logger = logging.getLogger('ares')
    root_logger.setLevel(level)

    # Avoid duplicate handlers on reload
    if root_logger.handlers:
        root_logger.handlers.clear()

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(logging.Formatter(
        '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
        datefmt='%H:%M:%S',
    ))
    root_logger.addHandler(console)

    # System log file
    sys_handler = logging.FileHandler(
        log_dir / 'system.log', encoding='utf-8',
    )
    sys_handler.setLevel(level)
    sys_handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    ))
    root_logger.addHandler(sys_handler)

    # Error-only log file
    err_handler = logging.FileHandler(
        log_dir / 'errors.log', encoding='utf-8',
    )
    err_handler.setLevel(logging.ERROR)
    err_handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    ))
    root_logger.addHandler(err_handler)


def main():
    print()
    print("  +==========================================+")
    print("  |   ARES - Adaptive Reasoning Executive    |")
    print("  |              System v0.1                 |")
    print("  +==========================================+")
    print()

    # Load configuration
    config_path = PROJECT_ROOT / 'config.yaml'
    settings = Settings.load(str(config_path))

    # Initialize logging
    setup_logging(settings)
    logger = logging.getLogger('ares')
    logger.info("ARES starting up")
    logger.info(f"LLM Provider: {settings.llm.provider} | Model: {settings.llm.model}")

    # Initialize orchestrator (coordinates all modules)
    try:
        orchestrator = Orchestrator(settings)
    except Exception as e:
        logger.critical(f"Failed to initialize orchestrator: {e}")
        print(f"\n  [ERROR] {e}")
        sys.exit(1)

    # Initialize UI
    api = AresAPI(orchestrator)
    window = create_window(settings, api)

    logger.info("Launching desktop UI")
    print("  System online. Launching interface...\n")

    # Start the UI event loop (blocks until window closes)
    start(debug=False)

    logger.info("ARES shutdown complete")


if __name__ == '__main__':
    main()
