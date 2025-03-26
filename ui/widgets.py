import logging
from abc import abstractmethod
from enum import Enum
from tkinter import BooleanVar, Toplevel
from tkinter import Button as tkButton
from tkinter import DoubleVar, IntVar, StringVar, Variable, filedialog
from tkinter import Label as tkLabel
from tkinter.colorchooser import askcolor
from tkinter.ttk import (
    Button,
    Checkbutton,
    Combobox,
    Entry,
    Frame,
    Label,
    LabelFrame,
    Spinbox,
    Widget,
)
from typing import Any, Dict, Tuple, Type, Union

from annotated_types import Gt, Lt, MultipleOf
from pydantic.fields import FieldInfo
from pydantic_extra_types.color import Color

from interfaces.widgets import IConfigField, IConfigGroup
from models.trackable_base_model import TrackableBaseModel
from models.widgets import WidgetInfo
from modules.config import config


class ToolTip:
    def __init__(self, widget, text):
        self._widget:Widget = widget
        self._text = text
        self._tooltip = None

        # Bind events to show/hide the tooltip
        self._widget.bind("<Enter>", self._show_tooltip)
        self._widget.bind("<Leave>", self._hide_tooltip)

    def _show_tooltip(self, event):
        # Create a tooltip when mouse enters the widget
        x, y, c, r = self._widget.bbox("insert")  # Get the position of the widget
        x += self._widget.winfo_rootx()  # Add a little offset
        y += self._widget.winfo_rooty() + self._widget.winfo_height()
        self._tooltip = Toplevel(self._widget)
        self._tooltip.wm_overrideredirect(True)  # Remove window borders
        self._tooltip.wm_geometry(f"+{x}+{y}")

        label = tkLabel(
            self._tooltip,
            text=self._text,
            # background="lightyellow",
            relief="solid",
            padx=5,
            pady=3,
        )
        label.pack()

    def _hide_tooltip(self, event):
        # Destroy the tooltip when mouse leaves the widget
        if self._tooltip:
            self._tooltip.destroy()
            self._tooltip = None


class ConfigField(IConfigField, Frame):
    _variable: Variable = None
    _widget: Widget = None
    _field: str = None
    _info: FieldInfo = None
    _type: Type = None

    @property
    def variable(self):
        """Property to get the variable."""
        return self._variable

    @property
    def widget(self):
        """Property to get the widget."""
        return self._widget

    @property
    def field(self):
        """Property to get the field name."""
        return self._field

    @property
    def info(self):
        """Property to get the field info."""
        return self._info

    @property
    def type(self):
        """Property to get the field type."""
        return self._type

    @property
    def value(self):
        """Property to get and set the value of the entry."""
        return self._variable.get()

    @value.setter
    def value(self, value):
        """Setter for the value property."""
        self._variable.set(value)

    @property
    def width(self):
        """Return the width of the widget."""
        return self._widget.winfo_width()

    @width.setter
    def width(self, width):
        """Set the width of the widget."""
        self._widget.config(width=width)

    def __init__(
        self,
        parent: Union[Frame, LabelFrame],
        field: Union[str, Tuple[Any, FieldInfo]],
        show_label: bool = True,
    ):
        """
        Initialize the config field with a parent frame and field name.

        Args:
            parent (Frame): The parent frame for this widget.
            field (str)|Tuple[Any, FieldInfo]: The configuration field name or a tuple of value and FieldInfo.
            show_label (bool): Whether to show a label for the field. Defaults to True.
        """
        super().__init__(parent)
        if isinstance(field, str):
            value, info = config.get(field)
        else:
            value, info = field

        self._show_label = show_label
        self._field = info.json_schema_extra["mapping"]
        self._info = info

        # Determine the type of the value and create the appropriate variable
        self._type = type(value)
        if self._type is bool:
            self._variable = BooleanVar(value=value)
        elif self._type is int:
            self._variable = IntVar(value=value)
        elif self._type is float:
            self._variable = DoubleVar(value=value)
        elif self._type is Color:
            self._variable = StringVar(value=str(value.as_hex("long")))
        else:
            self._variable = StringVar(value=str(value))
        self._variable.trace_add("write", self._on_value_change)

        self._init_ui(info)

        config.subscribe(self._on_config_change)

        # self._widget.bind()

        logging.debug(
            f"Created {self._type} field for {self.field} with initial value: {value}"
        )

    def _init_ui(self, info: FieldInfo):
        """
        Initialize the UI elements for the config field.

        Args:
            info (FieldInfo): Metadata about the field.

        Raises:
            Exception: If there is an error initializing the UI.
        """
        if self._show_label:
            self._label = Label(self, text=f"{info.title}:")
            self._label.pack(side="left", padx=(10, 0), anchor="w")

        self._create_ui(info)

        self._tooltip = ToolTip(self._widget, info.description)

    @abstractmethod
    def _create_ui(self, info: FieldInfo):
        """
        Create the UI elements for the config field.

        Args:
            value: The initial value for the field.
            info (FieldInfo): Metadata about the field.
        """
        pass

    def _on_value_change(self, *args):
        """
        Handle changes to the entry widget.

        Args:
            *args: Arguments passed by the trace callback.
        """
        value = self._variable.get()
        self._set_value(value)
        logging.debug(f"Value changed for field: {self._widget}, new value: {value}")

    def _on_config_change(self, field: str, value: Any):
        """
        Handle changes to the config value.

        Args:
            field (str): The field name that changed.
            value (Any): The new value.
        """
        if field == self.field:
            if isinstance(self._variable, StringVar):
                typeed_value = str(value)
            else:
                typeed_value = self._type(value)
            self._variable.set(typeed_value)
            logging.debug(f"Config value changed for field: {self._widget}")

    def _set_value(self, value):
        """
        Set the value of the config field.

        Args:
            value: The new value to set.

        Raises:
            Exception: If there is an error setting the value.
        """
        try:
            typeed_value = self._type(value)
            config.set(self.field, typeed_value)
            logging.debug(f"Setting value for field: {self._widget}, value: {value}")
        except Exception as e:
            logging.error(f"Error setting config value: {e}")


class TextField(ConfigField):
    """Class to handle text fields in the UI."""

    def _create_ui(self, info: FieldInfo):
        """
        Create the UI elements for the text field.

        Args:
            info (FieldInfo): Metadata about the field.
        """
        self._widget = Entry(self, textvariable=self._variable)
        self._widget.pack(side="left", fill="x", expand=True)


class ComboBoxField(ConfigField):
    """Class to handle combo box fields in the UI."""

    _values: list = []

    @property
    def values(self):
        """Property to get and set the values of the combo box."""
        return self._values

    @values.setter
    def values(self, values):
        """Setter for the values property."""
        self._values = values
        if self._widget:
            self._widget["values"] = values

    def __init__(
        self,
        parent: Union[Frame, LabelFrame],
        field: Union[str, Tuple[Any, FieldInfo]],
        values: list = [],
        show_label: bool = True,
    ):
        """
        Initialize the combo box field.

        Args:
            parent (Frame): The parent frame for this widget.
            field (str)|Tuple[Any, FieldInfo]: The configuration field name or a tuple of value and FieldInfo.
            values (list): The list of values for the combo box.
        """
        super().__init__(parent, field, show_label)
        self.values = values

    def _create_ui(self, info: FieldInfo):
        """
        Create the UI elements for the combo box field.

        Args:
            info (FieldInfo): Metadata about the field.
        """
        self._widget = Combobox(
            self,
            textvariable=self._variable,
            values=self.values,
            state="readonly",
        )
        self._widget.pack(side="right", padx=5, anchor="e")


class EnumComboBoxField(ComboBoxField):
    """Class to handle combo box fields for Enum values."""

    def __init__(
        self,
        parent: Union[Frame, LabelFrame],
        field: Union[str, Tuple[Any, FieldInfo]],
        show_label: bool = True,
    ):
        """
        Initialize the enum combo box field.

        Args:
            parent (Frame): The parent frame for this widget.
            field (str)|Tuple[Any, FieldInfo]: The configuration field name or a tuple of value and FieldInfo.
        """
        super().__init__(parent, field, show_label=show_label)
        if issubclass(self._type, Enum) or self._type is Enum:
            self.values = [
                e.value for e in self._type
            ]  # Extract string values from Enum
        else:
            msg = f"Type must be Enum. Got {self._type} on field {self.field}"
            logging.error(msg)
            raise TypeError(msg)


class FilePathField(TextField):
    """Class to handle file path fields in the UI."""

    def __init__(
        self,
        parent: Union[Frame, LabelFrame],
        field: Union[str, Tuple[Any, FieldInfo]],
        show_label: bool = True,
    ):
        """
        Initialize the file path field.

        Args:
            parent (Frame): The parent frame for this widget.
            field (str)|Tuple[Any, FieldInfo]: The configuration field name or a tuple of value and FieldInfo.
        """
        super().__init__(parent, field, show_label)

    def _create_ui(self, info: FieldInfo):
        """
        Create the UI elements for the file path field.

        Args:
            info (FieldInfo): Metadata about the field.
        """
        super()._create_ui(info)
        self._widget.config(state="readonly")
        self._browse_button = Button(
            self,
            text="Browse",
            command=self._browse_file,
        )
        self._browse_button.pack(side="left", padx=5)

    def _browse_file(self):
        """
        Open a file dialog to select a file.

        Raises:
            Exception: If there is an error selecting a file.
        """
        file_path = filedialog.askopenfilename()
        if file_path:
            self._variable.set(file_path)
        logging.debug(f"Browsing file for field: {self._widget}")


class SwitchButton(ConfigField):
    """Class to handle switch button fields in the UI."""

    def __init__(
        self,
        parent: Union[Frame, LabelFrame],
        field: Union[str, Tuple[Any, FieldInfo]],
        show_label: bool = True,
    ):
        """
        Initialize the switch button field.

        Args:
            parent (Frame): The parent frame for this widget.
            field (str)|Tuple[Any, FieldInfo]: The configuration field name or a tuple of value and FieldInfo.
        """
        super().__init__(parent, field, show_label)

    def _create_ui(self, info: FieldInfo):
        """
        Create the UI elements for the switch button field.

        Args:
            info (FieldInfo): Metadata about the field.
        """
        self._widget = Checkbutton(
            self,
            text=info.title if not self._show_label else "",
            style="Switch.TCheckbutton",
            variable=self._variable,
            offvalue=False,
            onvalue=True,
        )
        self._widget.pack(side="right", padx=5, anchor="e")

    def _toggle_value(self):
        """
        Toggle the value of the switch button.
        """
        self.value = not self.value


class SpinBoxField(ConfigField):
    """Class to handle spin box fields in the UI."""

    def __init__(
        self,
        parent: Union[Frame, LabelFrame],
        field: Union[str, Tuple[Any, FieldInfo]],
        show_label: bool = True,
    ):
        """
        Initialize the spin box field.

        Args:
            parent (Frame): The parent frame for this widget.
            field (str)|Tuple[Any, FieldInfo]: The configuration field name or a tuple of value and FieldInfo.
        """
        super().__init__(parent, field, show_label)

    def _create_ui(self, info: FieldInfo):
        """
        Create the UI elements for the spin box field.

        Args:
            info (FieldInfo): Metadata about the field.
        """
        min, max, increment = 0, int(2**31 - 1), 1.0

        for data in info.metadata:
            if isinstance(data, Gt):
                min = data.gt + 1
            elif isinstance(data, Lt):
                max = data.lt - 1
            elif isinstance(data, MultipleOf):
                increment = float(data.multiple_of)

        self._widget = Spinbox(
            self,
            textvariable=self._variable,
            from_=min,
            to=max,
            increment=increment,
        )
        self._widget.pack(side="right", padx=5, anchor="e")


class ColorField(TextField):
    """Class to handle color fields in the UI."""

    def __init__(
        self,
        parent: Union[Frame, LabelFrame],
        field: Union[str, Tuple[Any, FieldInfo]],
        show_label: bool = True,
    ):
        """
        Initialize the color field.

        Args:
            parent (Frame): The parent frame for this widget.
            field (str)|Tuple[Any, FieldInfo]: The configuration field name or a tuple of value and FieldInfo.
        """
        super().__init__(parent, field, show_label)

    def _create_ui(self, info: FieldInfo):
        """
        Create the UI elements for the color field.

        Args:
            info (FieldInfo): Metadata about the field.
        """
        self._color_button = tkButton(
            self,
            text="    ",
            command=self._choose_color,
            background=self.value,
        )
        # self._color_button.configure(back)
        self._color_button.pack(side="right", padx=5)
        super()._create_ui(info)
        self._widget.config(state="readonly")
        self._widget.pack(side="right", fill="none", expand=False)
        self.variable.trace_add("write", self._on_color_change)

    def _on_color_change(self, *args):
        """
        Handle changes to the color field.

        Args:
            *args: Arguments passed by the trace callback.
        """
        self._color_button.config(background=self.value)

    def _choose_color(self):
        """
        Open a color dialog to select a color.

        Raises:
            Exception: If there is an error selecting a color.
        """
        # Open the color picker dialog, Returns a tuple (rgb, hex)
        color_code = askcolor(
            title="Choose a color",
            initialcolor=self._variable.get(),
        )[1]
        if color_code:
            self.value = color_code
        else:
            logging.debug(f"Color dialog canceled for field: {self._widget}")


class ConfigGroup(IConfigGroup, LabelFrame):
    """Class to handle a group of configuration fields in the UI."""

    widgets: Dict[str, WidgetInfo] = {}

    def __init__(
        self,
        parent: Union[Frame, LabelFrame],
        model_field: Union[str, Tuple[TrackableBaseModel, FieldInfo]],
        width=10,
    ):
        """
        Initialize the config group with a parent frame and field name.

        Args:
            parent (Frame): The parent frame for this widget.
            model_field (str)|Tuple[TrackableBaseModel, FieldInfo]: The configuration field name or a tuple of value and FieldInfo.
            width (int): The width of the widgets except TextField and FilePathField. Defaults to 10.
        """
        model: TrackableBaseModel
        info: FieldInfo
        if isinstance(model_field, str):
            model, info = config.get(model_field)
        else:
            model, info = model_field

        super().__init__(parent, text=info.title)

        logging.debug(f"Creating ConfigGroup with title: {info.title}")

        self.widgets = controls_from_model(self, model, width)
        # Replace pack with grid
        self.grid(sticky="ew", padx=10, pady=5)


def width_adjustment(widget_name: str, width: int):
    """
    Adjust the width of the widget based on the widget name.

    Args:
        widget_name (str): The name of the widget.
        width (int): The width of the widget.

    Returns:
        int: The adjusted width of the widget.
    """
    if widget_name in ["Text", "File"]:
        return 0
    if widget_name == "Spinner":
        return width - 4
    return width


def controls_from_model(
    parent: Union[Frame, LabelFrame], model: TrackableBaseModel, width=10
) -> Dict[str, WidgetInfo]:
    """Create controls from a model."""
    widgets: Dict[str, WidgetInfo] = {}
    show_advanced = config.settings.showadvancedsettings

    row = 0  # Track the row for grid placement
    for field_name, field_info in model.model_fields.items():
        widget_name = field_info.json_schema_extra["widget"]
        advanced = field_info.json_schema_extra.get("advanced", True)

        if not widget_name:
            logging.warning(
                f"Widget type not specified for field '{field_name}'. Skipping."
            )
            continue

        if widget_name not in control_mapping:
            logging.warning(
                f"Widget type '{widget_name}' not found for field '{field_name}'."
            )
            continue

        widget_class = control_mapping[widget_name]
        widget = widget_class(parent, (getattr(model, field_name), field_info), width)
        widget.width = width_adjustment(widget_name, width)

        # Place the widget in the grid
        widget.grid(row=row, column=0, sticky="ew", padx=10, pady=5)
        if not (show_advanced or not advanced):
            widget.grid_remove()  # Hide advanced widgets if show_advanced is False

        # Store the widget and its advanced status
        widgets[field_name] = WidgetInfo(widget=widget, advanced=advanced, row=row)
        logging.debug(f"Adding widget: {widget} for field: {field_name}")

        row += 1  # Increment the row for the next widget

    # Configure grid column to expand
    parent.grid_columnconfigure(0, weight=1)

    return widgets


def toggle_advanced_widgets(
    parent: Union[Frame, LabelFrame],
    widgets: Dict[str, WidgetInfo],
    show_advanced: bool,
):
    """
    Toggle the visibility of advanced widgets while maintaining their position.

    Args:
        widgets (Dict[str, Dict[str, Any]]): A dictionary of widgets with their advanced status and grid row.
        show_advanced (bool): Whether to show advanced widgets.
    """
    for field_name, widget_info in widgets.items():
        widget = widget_info.widget
        advanced = widget_info.advanced

        if advanced and not show_advanced:
            widget.grid_remove()  # Hide the widget
            logging.debug(f"Hiding advanced widget: {field_name}")
        elif advanced and show_advanced:
            widget.grid()  # Show the widget in its original position
            logging.debug(f"Showing advanced widget: {field_name}")

        if isinstance(widget, IConfigGroup):
            toggle_advanced_widgets(widget, widget.widgets, show_advanced)

    parent.update_idletasks()


control_mapping: Dict[str, Union[IConfigField, IConfigGroup]] = {
    "Text": TextField,
    "EnumCombo": EnumComboBoxField,
    "Combo": ComboBoxField,
    "File": FilePathField,
    "Group": ConfigGroup,
    "Switch": SwitchButton,
    "Spinner": SpinBoxField,
    "Color": ColorField,
}
