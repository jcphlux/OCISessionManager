from abc import ABC, abstractmethod
from tkinter import Variable
from tkinter.ttk import Frame, LabelFrame, Widget
from typing import Any, Dict, Union

from pydantic.fields import FieldInfo


class IWidgetInfo(ABC):
    """Interface for the WidgetInfo class."""
    widget: Union["IConfigField", "IConfigGroup"]
    advanced: bool
    row: int


class IConfigField(ABC, Frame):
    """Interface for the ConfigField class."""

    @property
    @abstractmethod
    def variable(self) -> Variable:
        """Property to get the variable."""
        pass

    @property
    @abstractmethod
    def widget(self) -> Widget:
        """Property to get the widget."""
        pass

    @property
    @abstractmethod
    def field(self) -> str:
        """Property to get the field name."""
        pass

    @property
    @abstractmethod
    def info(self) -> FieldInfo:
        """Property to get the field info."""
        pass

    @property
    @abstractmethod
    def type(self):
        """Property to get the field type."""
        pass

    @property
    @abstractmethod
    def value(self):
        """Property to get and set the value of the entry."""
        pass

    @value.setter
    @abstractmethod
    def value(self, value):
        pass

    @property
    @abstractmethod
    def width(self) -> int:
        """Return the width of the widget."""
        pass

    @width.setter
    @abstractmethod
    def width(self, width: int):
        pass

    @abstractmethod
    def _on_value_change(self, *args):
        """Handle changes to the entry widget."""
        pass

    @abstractmethod
    def _on_config_change(self, field: str, value: Any):
        """Handle changes to the config value."""
        pass

    @abstractmethod
    def _set_value(self, value):
        """Set the value of the config field."""
        pass


class IConfigGroup(ABC, LabelFrame):
    """Interface for the ConfigGroup class."""

    @property
    @abstractmethod
    def widgets(self) -> Dict[str, IWidgetInfo]:
        """Property to get the widgets in the group."""
        pass
