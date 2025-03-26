import logging
import platform
import threading
from tkinter import PhotoImage, Tk, messagebox
from tkinter.ttk import Frame, Notebook
from typing import Tuple

import pystray
from PIL import Image
from pystray import MenuItem as item
from pystray._base import Icon

from interfaces.app import IApp
from modules.config import APP_NAME, config  # Import config instance
from modules.ssh_connection import SSHConnection
from modules.utils import image_path
from ui.connection_tab import ConnectionTab
from ui.logging_tab import LoggingTab
from ui.settings_tab import SettingsTab
from ui.theme import ThemeManager


class App(IApp, Frame):
    """Main application class."""

    connection_tab: ConnectionTab
    menu: Tuple[item, item, item] = None
    notebook: Notebook
    root: Tk
    settings_tab: SettingsTab
    ssh: SSHConnection
    theme: ThemeManager
    tray_icon: Icon = None
    tray_thread: threading.Thread = None
    visible = True
    _geometry_save_timer: threading.Timer = None
    _geometry_save_debounce = config.ui.savedebouncems

    def __init__(self, parent: Tk):
        """Initialize the App."""
        logging.debug("Initializing App.")
        Frame.__init__(self, parent)  # Explicitly initialize Frame
        self.root = parent
        self.theme = ThemeManager(self.root)
        self.root.title(APP_NAME)

        self.ssh = SSHConnection()
        self.ssh.register_connection_callback(self.on_connection_change)

        # Restore window geometry from config
        self.root.geometry(config.ui.geometry)

        # Create a notebook (tabbed interface)
        self.notebook = Notebook(self)
        self.notebook.pack(expand=True, fill="both")

        # Create content for each tab
        self.connection_tab = ConnectionTab(self)
        self.settings_tab = SettingsTab(self)
        self.logging_tab = LoggingTab(self)

        # Set the icon initially to red
        self.on_connection_change(False)

        self.check_settings_and_disable_connection_tab()

        # Initial tray icon setup
        if platform.system() in ["Windows", "Linux", "Darwin"]:  # Darwin = macOS
            try:
                self.tray_icon = pystray.Icon(
                    "SSHMonitor", self.icon_image, "SSH Monitor", self.menu
                )
                self.tray_icon.run_detached()
                self.root.protocol(
                    "WM_DELETE_WINDOW", self.hide
                )  # Hide the window on close
            except Exception as e:
                logging.warning(f"System tray is not supported on this platform: {e}")
                self.root.protocol(
                    "WM_DELETE_WINDOW", self.quit
                )  # Exit the app on close
        else:
            logging.warning("System tray is not supported on this platform.")
            self.root.protocol("WM_DELETE_WINDOW", self.quit)  # Exit the app on close

        self.root.after(
            1000, lambda: self.on_connection_change(False)
        )  # Set the initial icon state

        # Bind events to save geometry on resize or move
        self.root.after(
            1500, lambda: self.root.bind("<Configure>", self.save_geometry)
        )  # Delay binding to avoid immediate save on startup

    def create_tray(self):
        """Creates and runs the system tray icon."""
        logging.debug("Creating system tray icon.")

    def check_settings_and_disable_connection_tab(self):
        """Disable the connection tab if any settings values are empty."""
        logging.debug("Checking settings to enable/disable connection tab.")

        if self.settings_tab.valid:
            logging.debug("Enabling connection tab.")
            self.notebook.tab(0, state="normal")

        else:
            logging.debug("Disabling connection tab due to empty settings.")
            self.notebook.tab(0, state="disabled")

        self.update_tray_menu()

    def hide(self):
        """Hide the UI window."""
        if self.tray_icon:
            logging.debug("Hiding the UI window.")
            self.visible = False
            self.root.withdraw()
        else:
            logging.debug("Tray icon not supported, exiting the application.")
            self.quit()

    def show(self):
        """Show the UI window."""
        logging.debug("Showing the UI window.")

        def _show():
            self.root.protocol("WM_DELETE_WINDOW", self.hide)
            self.root.deiconify()
            self.visible = True

        self.root.after(0, _show)

    def update_tray_menu(self):
        """Update the tray menu to reflect the current connection state."""
        logging.debug("Updating tray menu.")
        connect_label = "Disconnect" if self.ssh.connected else "Connect"
        connect_enabled = self.settings_tab and self.settings_tab.valid
        self.menu = (
            item("Open Config", self.show, default=True),
            item(connect_label, self.ssh.toggle, enabled=self.settings_tab.valid),
            item("Quit", self.quit),
        )

        if self.tray_icon:
            self.tray_icon.menu = pystray.Menu(*self.menu)

    def connect_disabled(self):
        """display a msgbox if the connection tab is disabled."""
        logging.debug("Connection tab is disabled, showing message box.")
        messagebox.showinfo(
            "Connection Disabled",
            "Please fill in all settings before connecting.",
        )

    def on_connection_change(self, connected: bool):
        """Update the icon to green for connected."""
        logging.debug(
            f"Connection status changed: {'connected' if connected else 'disconnected'}."
        )
        img_path = image_path("green" if connected else "red")
        self.root.iconbitmap(False, img_path)
        self.icon_image = Image.open(img_path)

        img = PhotoImage(file=img_path)
        self.root.iconphoto(False, img)

        if self.tray_icon:
            self.tray_icon.icon = self.icon_image  # Update the tray icon dynamically

        self.update_tray_menu()  # Ensure the tray menu reflects the connection state

    def save_geometry(self, event=None):
        """Debounced save of the current window geometry to the config."""
        if self.root.state() == "normal":  # Only save if not minimized
            if self._geometry_save_timer:
                self._geometry_save_timer.cancel()  # Cancel any existing timer
            self._geometry_save_timer = threading.Timer(
                self._geometry_save_debounce, self._save_geometry_now
            )
            self._geometry_save_timer.start()

    def _save_geometry_now(self):
        """Save the current window geometry to the config immediately."""
        geometry = self.root.geometry()
        config.set("ui.geometry", geometry)

    def quit(self):
        """Quit the application cleanly."""
        logging.debug("Quitting application.")

        # Save geometry immediately before quitting
        if self._geometry_save_timer:
            self._geometry_save_timer.cancel()
            self._save_geometry_now()
        if self.tray_icon:
            self.tray_icon.stop()  # Stop the tray icon
        self.root.quit()
