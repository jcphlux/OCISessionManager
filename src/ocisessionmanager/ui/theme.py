import platform
import time
from sys import getwindowsversion
from threading import Event, Thread
from tkinter import Tk

import darkdetect
import pywinstyles
import sv_ttk

from ocisessionmanager.models.config.enums import Theme
from ocisessionmanager.modules.config import config


class ThemeManager:
    """Class to manage themes in the application."""

    _root: Tk
    _theme: Theme = Theme.SYSTEM
    _stop_event: Event = Event()
    _system_theme_thread: Thread = None
    _theme_key: str = config.ui.model_fields["theme"].json_schema_extra["mapping"]

    def __init__(self, root: Tk):
        self._root = root
        config.subscribe(self._on_config_change)
        self.apply_theme(config.ui.theme)

    def apply_theme(self, theme: Theme):
        """Apply the provided theme and start/stop system theme monitoring."""
        mode = "dark" if theme == Theme.DARK else "light"
        if theme == Theme.SYSTEM:
            mode = str(darkdetect.theme()).lower()
            self._start_monitoring_system_theme()
        else:
            self._stop_monitoring_system_theme()  # Stop monitoring system theme

        self._root.after(10, self._apply_system_theme, mode)

    def _on_config_change(self, key: str, value):
        """Handle configuration changes."""
        if key == self._theme_key:
            self.apply_theme(value)
        if key in ["ui.darktilebarcolor", "ui.lighttilebarcolor"]:
            if self._theme == Theme.SYSTEM:
                mode = str(darkdetect.theme()).lower()
            else:
                mode = "dark" if self._theme == Theme.DARK else "light"
            self._root.after(10, self._apply_system_theme, mode)

    def _apply_system_theme(self, mode: str):
        """Apply system theme based on darkdetect."""
        sv_ttk.set_theme(mode, self._root)
        self._apply_theme_to_titlebar(mode)

    def _apply_theme_to_titlebar(self, mode: str):
        """Apply titlebar color based on the theme (Windows-specific)."""
        if platform.system() != "Windows":
            # Skip titlebar customization on non-Windows platforms
            return

        version = getwindowsversion()
        is_dark = mode == "dark"
        if version.major == 10 and version.build >= 22000:
            titlebar_color = (
                config.ui.darktilebarcolor.as_hex("long")
                if is_dark
                else config.ui.lighttilebarcolor.as_hex("long")
            )
            pywinstyles.change_header_color(self._root, titlebar_color)
        elif version.major == 10:
            pywinstyles.change_header_color(self._root, "dark" if is_dark else "normal")
            # A hacky way to update the title bar's color on Windows 10 (it doesn't update instantly like on Windows 11)
            self._root.wm_attributes("-alpha", 0.99)
            self._root.wm_attributes("-alpha", 1)

    def _start_monitoring_system_theme(self):
        """Start monitoring for system theme changes."""
        if (
            self._system_theme_thread is None
            or not self._system_theme_thread.is_alive()
        ):
            self._system_theme_thread = Thread(
                target=self._monitor_system_theme, daemon=True
            )
            self._system_theme_thread.start()

    def _stop_monitoring_system_theme(self):
        """Stop monitoring for system theme changes."""
        self._stop_event.set()  # Signal the thread to stop monitoring
        if self._system_theme_thread is not None:
            self._system_theme_thread.join()  # Wait for the thread to finish gracefully

    def _monitor_system_theme(self):
        """Monitor for system theme changes and update the app's theme."""
        last_known_theme = ""

        while not self._stop_event.is_set():
            current_system_theme = str(darkdetect.theme()).lower()
            if current_system_theme != last_known_theme:
                print(
                    f"System theme changed to {current_system_theme}. Applying theme..."
                )

                # Schedule the theme application on the main thread
                self._root.after(10, self._apply_system_theme, current_system_theme)
                last_known_theme = current_system_theme
            time.sleep(config.ui.system_monitor_interval)

    def _stop_monitoring(self):
        """Stop monitoring the system theme."""
        self._stop_event.set()
