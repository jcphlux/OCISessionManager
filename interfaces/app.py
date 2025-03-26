import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from tkinter import Tk
from tkinter.ttk import Frame, Notebook
from typing import Tuple

from pystray import MenuItem as item
from pystray._base import Icon

from interfaces.connection_tab import IConnectionTab
from interfaces.settings_tab import ISettingsTab
from modules.ssh_connection import SSHConnection
from ui.theme import ThemeManager


@dataclass
class IApp(ABC, Frame):
    connection_tab: IConnectionTab = field(init=False)
    menu: Tuple[item, item] = field(init=False)
    notebook: Notebook = field(init=False)
    root: Tk = field(init=False)
    settings_tab: ISettingsTab = field(init=False)
    ssh: SSHConnection = field(init=False)
    theme: ThemeManager = field(init=False)
    tray_icon: Icon = field(init=False)
    tray_thread: threading.Thread = field(init=False)
    visible: bool = field(init=False)

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def hide(self):
        pass

    @abstractmethod
    def show(self):
        pass

    @abstractmethod
    def on_connection_change(self, connected: bool):
        pass

    @abstractmethod
    def check_settings_and_disable_connection_tab(self):
        pass

    @abstractmethod
    def quit(self):
        pass
