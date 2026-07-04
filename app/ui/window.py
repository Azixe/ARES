"""
ARES UI Window
Sets up the pywebview native desktop window.
"""

import logging
from pathlib import Path

import webview

from app.config.settings import Settings

logger = logging.getLogger('ares.ui')

# Path to the web UI directory
WEB_DIR = Path(__file__).parent / 'web'


def create_window(settings: Settings, api) -> webview.Window:
    """Create the pywebview native window.

    Args:
        settings: Application settings.
        api: AresAPI instance to expose to JavaScript.

    Returns:
        The created window object.
    """
    index_path = WEB_DIR / 'index.html'

    if not index_path.exists():
        raise FileNotFoundError(f"UI entry point not found: {index_path}")

    # Use file:/// URL for local HTML — convert backslashes for Windows
    url = index_path.as_uri()

    window = webview.create_window(
        title=settings.ui.title,
        url=url,
        js_api=api,
        width=settings.ui.width,
        height=settings.ui.height,
        min_size=(700, 500),
        background_color='#0a0a0f',
        text_select=True,
    )

    api.set_window(window)
    logger.info(f"Window created: {settings.ui.width}x{settings.ui.height}")
    return window


def start(debug: bool = False):
    """Start the pywebview event loop. Blocks until window is closed."""
    logger.info("Starting UI event loop")
    webview.start(debug=debug)
    logger.info("UI event loop ended")
