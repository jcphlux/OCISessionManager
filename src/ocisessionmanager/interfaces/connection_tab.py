from abc import ABC, abstractmethod
from tkinter.ttk import Frame


class IConnectionTab(ABC, Frame):
    """Interface for the ConnectionTab class."""

    @abstractmethod
    def create_ui(self):
        pass

    @abstractmethod
    def on_connection_change(self, connected: bool):
        pass
