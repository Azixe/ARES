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

    def get_desktop_info(self):
        """Get desktop awareness data for UI display. Called from JavaScript."""
        try:
            snapshot = self.orchestrator.get_desktop_snapshot()
            # Simplify for UI consumption
            res = snapshot.get('resources', {})
            win = snapshot.get('active_window', {})
            apps = snapshot.get('running_apps', [])

            return {
                'cpu_percent': res.get('cpu_percent', 0),
                'ram_percent': res.get('ram_percent', 0),
                'ram_used_gb': res.get('ram_used_gb', 0),
                'ram_total_gb': res.get('ram_total_gb', 0),
                'battery_percent': res.get('battery_percent'),
                'battery_plugged': res.get('battery_plugged'),
                'active_window': win.get('title', ''),
                'active_process': win.get('process', ''),
                'app_count': len(apps),
            }
        except Exception as e:
            logger.error(f"Desktop info failed: {e}")
            return {}
