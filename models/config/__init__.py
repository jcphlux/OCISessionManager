from pydantic import Field

from models.trackable_base_model import TrackableBaseModel

from .connectionsettings import ConnectionSettings
from .enums import LogLevel, Theme
from .keypaths import KeyPaths
from .settings import Settings
from .ui import UI


class ConfigModel(TrackableBaseModel):
    settings: Settings = Field(
        default_factory=Settings,
        description="Application settings",
        title="Settings",
        json_schema_extra={"widget": "Group", "advanced": False},
    )
    keypaths: KeyPaths = Field(
        default_factory=KeyPaths,
        description="Key paths configuration",
        title="Key Paths",
        json_schema_extra={"widget": "Group", "advanced": False},
    )
    connectionsettings: ConnectionSettings = Field(
        default_factory=ConnectionSettings,
        description="Connection settings",
        title="Connection Settings",
        json_schema_extra={"widget": "Group", "advanced": False},
    )
    ui: UI = Field(
        default_factory=UI,
        description="UI configuration",
        title="UI",
        json_schema_extra={"widget": "Group", "advanced": False},
    )


__all__ = [
    "ConfigModel",
    "ConnectionSettings",
    "KeyPaths",
    "Settings",
    "UI",
    Theme,
    LogLevel,
]
