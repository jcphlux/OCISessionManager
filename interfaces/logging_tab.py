from abc import ABC, abstractmethod
from tkinter.ttk import Frame


class ILoggingTab(ABC, Frame):
    """Interface for the ConnectionTab class."""

    @abstractmethod
    def create_ui(self):
        pass

    @abstractmethod
    def on_data_update(self, log_data: list):
        pass

    @abstractmethod
    def on_log_level_change(self, event):
        pass

    @abstractmethod
    def show_stack_trace(self, event):
        pass
