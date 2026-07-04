"""
ARES UI API
Python API class exposed to JavaScript via pywebview's js_api.
Handles all communication between the frontend and the orchestrator.
"""

import json
import logging
import traceback

from app.core.orchestrator import Orchestrator

logger = logging.getLogger('ares.ui')


class AresAPI:
    """API bridge between the web frontend and ARES backend.

    All public methods are callable from JavaScript via pywebview.api.*
    Methods run in separate threads automatically (pywebview behavior).
    """

    def __init__(self, orchestrator: Orchestrator):
        self.orchestrator = orchestrator
        self._window = None

    def set_window(self, window):
        """Set the pywebview window reference for JS callbacks."""
        self._window = window

    def _eval_js(self, code: str):
        """Execute JavaScript in the frontend."""
        if self._window:
            try:
                self._window.evaluate_js(code)
            except Exception as e:
                logger.error(f"JS evaluation failed: {e}")

    def _push_status(self, status: str):
        """Update the status indicator in the frontend."""
        self._eval_js(f'window.ares.updateStatus({json.dumps(status)})')

    def send_message(self, text: str):
        """Process a user message. Called from JavaScript.

        Streams the response back to the frontend chunk by chunk.
        """
        if not text or not text.strip():
            return

        text = text.strip()
        logger.info(f"User: {text[:100]}{'...' if len(text) > 100 else ''}")

        try:
            # Check API key
            if not self.orchestrator.settings.llm.api_key:
                self._eval_js(
                    'window.ares.showError('
                    '"No API key configured. Set ARES_API_KEY in your .env file '
                    'or as an environment variable.")'
                )
                return

            # Update status and signal response start
            self._push_status('thinking')
            self._eval_js('window.ares.startResponse()')

            # Stream response chunks to frontend
            for chunk in self.orchestrator.process_stream(text):
                escaped = json.dumps(chunk)
                self._eval_js(f'window.ares.appendChunk({escaped})')

            # Finalize
            self._eval_js('window.ares.finalizeResponse()')
            self._push_status('idle')

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Processing failed: {error_msg}\n{traceback.format_exc()}")
            self._eval_js(f'window.ares.showError({json.dumps(error_msg)})')
            self._push_status('error')

    def clear_history(self):
        """Clear conversation history. Called from JavaScript."""
        self.orchestrator.memory.clear()
        self._eval_js('window.ares.clearChat()')
        logger.info("History cleared by user")
        return True

    def get_status(self):
        """Get current system status. Called from JavaScript."""
        return self.orchestrator.get_status()

    def get_config_display(self):
        """Get safe config values for UI display. Called from JavaScript."""
        return {
            'model': self.orchestrator.settings.llm.model,
            'provider': self.orchestrator.settings.llm.provider,
            'has_key': bool(self.orchestrator.settings.llm.api_key),
            'streaming': self.orchestrator.settings.llm.streaming,
        }
