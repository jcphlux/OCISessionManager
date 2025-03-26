from dataclasses import dataclass
from typing import Union

from interfaces.widgets import IConfigField, IConfigGroup, IWidgetInfo


@dataclass
class WidgetInfo(IWidgetInfo):
    widget: Union[IConfigField, IConfigGroup]
    advanced: bool
    row: int
