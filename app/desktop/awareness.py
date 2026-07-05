"""
ARES Desktop Awareness Module
Read-only observation of the desktop environment.
ARES observes. It does not control.
"""

import ctypes
import ctypes.wintypes
import logging
import platform
from datetime import datetime

import psutil

logger = logging.getLogger('ares.desktop')


class DesktopAwareness:
    """Provides read-only awareness of the user's desktop environment.

    Collects system metrics, active window info, and running applications.
    All operations are non-invasive — no system state is modified.
    """

    def __init__(self):
        self._user32 = ctypes.windll.user32
        logger.info("Desktop awareness module initialized")

    # ── Active Window ────────────────────────────────────────────

    def get_active_window(self) -> dict:
        """Get the currently focused window's title and process."""
        try:
            hwnd = self._user32.GetForegroundWindow()
            if not hwnd:
                return {'title': 'Unknown', 'process': 'Unknown', 'pid': None}

            # Window title
            length = self._user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            self._user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value or 'Untitled'

            # Process info from window handle
            pid = ctypes.wintypes.DWORD()
            self._user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            process_name = 'Unknown'
            try:
                proc = psutil.Process(pid.value)
                process_name = proc.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

            return {
                'title': title,
                'process': process_name,
                'pid': pid.value,
            }
        except Exception as e:
            logger.error(f"Failed to get active window: {e}")
            return {'title': 'Error', 'process': 'Error', 'pid': None}

    # ── System Resources ─────────────────────────────────────────

    def get_system_resources(self) -> dict:
        """Get current CPU, memory, and disk usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            result = {
                'cpu_percent': cpu_percent,
                'ram_total_gb': round(memory.total / (1024 ** 3), 1),
                'ram_used_gb': round(memory.used / (1024 ** 3), 1),
                'ram_percent': memory.percent,
                'disk_total_gb': round(disk.total / (1024 ** 3), 1),
                'disk_used_gb': round(disk.used / (1024 ** 3), 1),
                'disk_percent': disk.percent,
            }

            # Battery (if available — laptops)
            battery = psutil.sensors_battery()
            if battery:
                result['battery_percent'] = battery.percent
                result['battery_plugged'] = battery.power_plugged

            return result
        except Exception as e:
            logger.error(f"Failed to get system resources: {e}")
            return {}

    # ── Running Applications ─────────────────────────────────────

    def get_running_applications(self) -> list[dict]:
        """Get user-visible applications currently running.

        Filters out system processes and background services to return
        only applications the user would recognize.
        """
        # Common background/system processes to exclude
        SYSTEM_PROCESSES = {
            'svchost.exe', 'csrss.exe', 'lsass.exe', 'smss.exe',
            'wininit.exe', 'services.exe', 'winlogon.exe', 'dwm.exe',
            'conhost.exe', 'fontdrvhost.exe', 'sihost.exe', 'taskhostw.exe',
            'ctfmon.exe', 'dllhost.exe', 'audiodg.exe', 'searchhost.exe',
            'startmenuexperiencehost.exe', 'runtimebroker.exe',
            'textinputhost.exe', 'shellexperiencehost.exe',
            'applicationframehost.exe', 'systemsettings.exe',
            'securityhealthservice.exe', 'securityhealthsystray.exe',
            'spoolsv.exe', 'wlanext.exe', 'dashost.exe',
            'searchindexer.exe', 'searchprotocolhost.exe',
            'searchfilterhost.exe', 'msdtc.exe', 'registry',
            'system', 'idle', 'system idle process', 'memory compression',
            'wmiprvse.exe', 'sgrmbroker.exe', 'compkggsrv.exe',
            'crashpad_handler.exe', 'msedgewebview2.exe',
        }

        apps = {}
        try:
            for proc in psutil.process_iter(['pid', 'name', 'status']):
                try:
                    info = proc.info
                    name = info['name'].lower() if info['name'] else ''

                    # Skip system processes
                    if name in SYSTEM_PROCESSES:
                        continue

                    # Skip processes without meaningful names
                    if not name or len(name) < 3:
                        continue

                    # Deduplicate by name (keep first instance)
                    display_name = info['name']
                    if display_name not in apps:
                        apps[display_name] = {
                            'name': display_name,
                            'pid': info['pid'],
                            'status': info['status'],
                        }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            return sorted(apps.values(), key=lambda x: x['name'].lower())
        except Exception as e:
            logger.error(f"Failed to get running applications: {e}")
            return []

    # ── Clipboard ────────────────────────────────────────────────

    def get_clipboard_text(self) -> str | None:
        """Get current clipboard text content.

        Returns None if clipboard is empty or contains non-text data.
        """
        try:
            CF_UNICODETEXT = 13

            if not ctypes.windll.user32.OpenClipboard(0):
                return None

            try:
                handle = ctypes.windll.user32.GetClipboardData(CF_UNICODETEXT)
                if not handle:
                    return None

                kernel32 = ctypes.windll.kernel32
                ptr = kernel32.GlobalLock(handle)
                if not ptr:
                    return None

                try:
                    text = ctypes.wstring_at(ptr)
                    # Truncate very long clipboard contents
                    if len(text) > 2000:
                        text = text[:2000] + '... [truncated]'
                    return text if text.strip() else None
                finally:
                    kernel32.GlobalUnlock(handle)
            finally:
                ctypes.windll.user32.CloseClipboard()
        except Exception as e:
            logger.debug(f"Clipboard read failed: {e}")
            return None

    # ── System Info ──────────────────────────────────────────────

    def get_system_info(self) -> dict:
        """Get static system information (OS, hardware, etc.)."""
        try:
            return {
                'os': f"{platform.system()} {platform.release()}",
                'os_version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'hostname': platform.node(),
                'python_version': platform.python_version(),
                'cpu_cores_physical': psutil.cpu_count(logical=False),
                'cpu_cores_logical': psutil.cpu_count(logical=True),
                'ram_total_gb': round(
                    psutil.virtual_memory().total / (1024 ** 3), 1
                ),
            }
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return {}

    # ── Composite Snapshot ───────────────────────────────────────

    def get_snapshot(self, include_clipboard: bool = False) -> dict:
        """Get a complete snapshot of the current desktop state.

        Args:
            include_clipboard: Whether to include clipboard contents.
                Disabled by default for privacy.

        Returns:
            Dict with all awareness data.
        """
        snapshot = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'active_window': self.get_active_window(),
            'resources': self.get_system_resources(),
            'running_apps': self.get_running_applications(),
        }

        if include_clipboard:
            clipboard = self.get_clipboard_text()
            if clipboard:
                snapshot['clipboard'] = clipboard

        return snapshot

    def format_context(self, include_clipboard: bool = False) -> str:
        """Format desktop awareness data as a context string for the LLM.

        This is the primary method used by the Orchestrator to inject
        desktop context into the prompt.
        """
        snapshot = self.get_snapshot(include_clipboard=include_clipboard)
        lines = []

        # Active window
        win = snapshot.get('active_window', {})
        if win.get('title'):
            lines.append(f"Active Window: {win['title']} ({win.get('process', '?')})")

        # System resources
        res = snapshot.get('resources', {})
        if res:
            parts = [f"CPU: {res.get('cpu_percent', '?')}%"]
            if 'ram_used_gb' in res:
                parts.append(
                    f"RAM: {res['ram_used_gb']}/{res['ram_total_gb']}GB "
                    f"({res.get('ram_percent', '?')}%)"
                )
            if 'battery_percent' in res:
                plug = 'Plugged' if res.get('battery_plugged') else 'Battery'
                parts.append(f"Power: {res['battery_percent']}% ({plug})")
            lines.append("System: " + " | ".join(parts))

        # Running apps (top-level names only, compact)
        apps = snapshot.get('running_apps', [])
        if apps:
            # Show only notable apps, not everything
            app_names = [a['name'].replace('.exe', '') for a in apps[:15]]
            lines.append(f"Running Apps: {', '.join(app_names)}")
            if len(apps) > 15:
                lines.append(f"  ... and {len(apps) - 15} more")

        # Clipboard
        if include_clipboard and 'clipboard' in snapshot:
            clip = snapshot['clipboard']
            # Show first 200 chars
            preview = clip[:200] + ('...' if len(clip) > 200 else '')
            lines.append(f"Clipboard: {preview}")

        return '\n'.join(lines)
