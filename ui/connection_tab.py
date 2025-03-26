import logging
import threading
from tkinter.ttk import Button, Frame

from interfaces.app import IApp
from interfaces.connection_tab import IConnectionTab


class ConnectionTab(IConnectionTab, Frame):
    """Class to handle the connection tab in the UI."""

    _app: IApp

    def __init__(self, app: IApp):
        """
        Initialize the connection tab.

        Args:
            app (IApp): The main application instance.
        """
        Frame.__init__(self, app.notebook)
        self._app = app
        self.create_ui()

    def create_ui(self):
        """Create the UI elements for the connection tab."""

        logging.debug("Initializing connection tab UI components")
        self._app.notebook.add(self, text="Connection")

        self.connect_button = Button(
            self,
            text="Connect",
            command=lambda: threading.Thread(
                target=self._app.ssh.toggle
            ).start(),  # Run ssh.toggle in a separate thread
        )
        self.connect_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        # Register callbacks
        self._app.ssh.register_connection_callback(self.on_connection_change)

    # Define callback functions
    def on_connection_change(self, connected: bool):
        """Update the connection button text."""
        logging.debug(
            f"Connection status changed: {'Connected' if connected else 'Disconnected'}"
        )
        if connected:
            self.connect_button.config(text="Disconnect")
            self._app.notebook.tab(self._app.settings_tab, state="disabled")
            logging.info(
                "Connection established, UI updated to reflect connection status."
            )
        else:
            self.connect_button.config(text="Connect")
            self._app.notebook.tab(self._app.settings_tab, state="normal")
            logging.info(
                "Connection terminated, UI updated to reflect disconnection status."
            )
