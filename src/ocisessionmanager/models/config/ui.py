from pydantic import Field, field_validator
from pydantic_extra_types.color import Color

from ocisessionmanager.models.config.enums import Theme
from ocisessionmanager.models.trackable_base_model import TrackableBaseModel


class UI(TrackableBaseModel):
    geometry: str = Field("700x570", description="Window geometry", title="Geometry")
    savedebouncems: float = Field(
        0.5,
        description="Save debounce interval in seconds",
        multiple_of=0.1,
        gt=0,
        lt=60,
        title="Save Debounce (s)",
        json_schema_extra={"widget": "Spinner", "advanced": True},
    )
    theme: Theme = Field(
        Theme.SYSTEM,
        description="UI theme",
        title="Theme",
        json_schema_extra={"widget": "EnumCombo", "advanced": False},
    )
    darktilebarcolor: Color = Field(
        Color("#1c1c1c"),
        description="Dark tile bar color",
        title="Dark Tile Bar Color",
        json_schema_extra={"widget": "Color", "advanced": True},
    )
    lighttilebarcolor: Color = Field(
        Color("#fafafa"),
        description="Light tile bar color",
        title="Light Tile Bar Color",
        json_schema_extra={"widget": "Color", "advanced": True},
    )
    system_monitor_interval: float = Field(
        5,
        description="Interval for system monitor updates when theme is set to system in seconds",
        multiple_of=0.1,
        gt=1,
        lt=60,
        title="System Monitor Interval (s)",
        json_schema_extra={"widget": "Spinner", "advanced": True},
    )

    @field_validator("theme")
    def validate_theme(cls, value):
        if value not in Theme:
            valid_themes = [theme.value for theme in Theme]
            raise ValueError(f"Theme must be one of {valid_themes}")
        return value
