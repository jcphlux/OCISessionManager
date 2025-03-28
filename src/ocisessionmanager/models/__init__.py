from pydantic import Field

from ocisessionmanager.models.trackable_base_model import TrackableBaseModel

from ocisessionmanager.models.config.connectionsettings import ConnectionSettings
from ocisessionmanager.models.config.enums import LogLevel, Theme
from ocisessionmanager.models.config.keypaths import KeyPaths
from ocisessionmanager.models.config.settings import Settings
from ocisessionmanager.models.config.ui import UI


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
