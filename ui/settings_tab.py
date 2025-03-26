import logging
from tkinter import Canvas
from tkinter.ttk import Frame, Scrollbar
from typing import Dict

from interfaces.app import IApp
from interfaces.settings_tab import ISettingsTab
from interfaces.widgets import IConfigField
from models.widgets import WidgetInfo
from modules.config import config
from ui.widgets import ConfigField, controls_from_model, toggle_advanced_widgets


class SettingsTab(ISettingsTab, Frame):
    """Class to handle the settings tab in the UI."""

    _app: IApp
    _unsaved_changes: bool
    _widgets: Dict[str, WidgetInfo] = {}

    @property
    def valid(self):
        return True
        # fields = [
        #     self.priv_key_path_entry.get(),
        #     self.pub_key_path_entry.get(),
        #     self.local_port_entry.get(),
        #     self.target_port_entry.get(),
        # ]
        # return not self._unsaved_changes and all(fields)

    def __init__(self, app: IApp):
        Frame.__init__(self, app.notebook)
        self._app = app
        self._unsaved_changes = False

        # Create a canvas and scrollbar for scrollable UI
        self.canvas = Canvas(self)
        self.scrollbar = Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: (
                self.canvas.configure(scrollregion=self.canvas.bbox("all")),
                self.canvas.itemconfig("window", width=self.canvas.winfo_width()),
            ),
        )
        self.canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw", tags="window"
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # Enable mouse scroll on canvas
        self.canvas.bind("<Enter>", lambda e: self._bind_mouse_scroll())
        self.canvas.bind("<Leave>", lambda e: self._unbind_mouse_scroll())

        self.create_ui()

    def _bind_mouse_scroll(self):
        self.canvas.bind_all("<MouseWheel>", self._on_mouse_scroll)

    def _unbind_mouse_scroll(self):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mouse_scroll(self, event):
        self.canvas.yview_scroll(-1 * (event.delta // 120), "units")

    def create_ui(self):
        logging.debug("Creating settings tab UI.")

        self._app.notebook.add(self, text="Settings")

        # Pass the scrollable frame instead of self
        self._widgets = controls_from_model(self.scrollable_frame, config)

        advanced_widget:IConfigField = self._widgets["settings"].widget.widgets[
            "showadvancedsettings"
        ].widget
        advanced_widget.variable.trace_add(
            "write",
            lambda *args: toggle_advanced_widgets(
                self.scrollable_frame, self._widgets, advanced_widget.value
            ),
        )

        self._app.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)
        logging.debug("Settings tab created successfully.")

    def on_tab_change(self, event):
        logging.debug("Tab changed.")
        # if self.notebook.index("current") == 1:  # Index 1 is the connection tab
        #     if not self.check_unsaved_changes() or not self.valid:
        #         logging.debug("Unsaved changes detected or invalid settings.")
        #         self.notebook.select(0)  # Revert to settings tab if unsaved changes
