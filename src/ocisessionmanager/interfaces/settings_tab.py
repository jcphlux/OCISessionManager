from abc import ABC, abstractmethod
from tkinter.ttk import Frame


class ISettingsTab(ABC, Frame):
    """Interface for the SettingsTab class."""

    @abstractmethod
    def create_ui(self):
        pass

    @abstractmethod
    def on_tab_change(self, event):
        pass
