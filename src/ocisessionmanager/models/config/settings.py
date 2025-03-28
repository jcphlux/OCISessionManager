from annotated_types import T
from pydantic import Field, field_validator

from ocisessionmanager.models.config.enums import LogLevel
from ocisessionmanager.models.trackable_base_model import TrackableBaseModel


class Settings(TrackableBaseModel):
    showadvancedsettings: bool = Field(
        False,
        description="Show advanced settings",
        title="Show Advanced Settings",
        json_schema_extra={"widget": "Switch", "advanced": False},
    )
    connectionmaxretries: int = Field(
        3,
        description="Maximum number of connection retries",
        multiple_of=1,
        gt=0,
        lt=10,
        title="Connection Max Retries",
        json_schema_extra={"widget": "Spinner", "advanced": True},
    )
    checkconnectioninterval: float = Field(
        10,
        description="Interval to check connection in seconds",
        multiple_of=0.1,
        gt=5,
        lt=100,
        title="Check Connection Interval (s)",
        json_schema_extra={"widget": "Spinner", "advanced": True},
    )
    displayloglevel: LogLevel = Field(
        LogLevel.INFO,
        description="Log level to display",
        title="Display Log Level",
        json_schema_extra={"widget": "EnumCombo", "advanced": False},
    )
    refreshloginterval: float = Field(
        10,
        description="Log refresh interval in seconds",
        multiple_of=0.1,
        gt=1,
        lt=60,
        title="Refresh Log Interval (s)",
        json_schema_extra={"widget": "Spinner", "advanced": True},
    )
    autoscrolllog: bool = Field(
        True,
        description="Enable auto-scrolling of logs",
        title="Auto Scroll Log",
        json_schema_extra={"widget": "Switch", "advanced": False},
    )
    autosavedebounceinterval: float = Field(
        2,
        description="Auto-save debounce interval in seconds",
        multiple_of=0.1,
        gt=1,
        lt=60,
        title="Auto Save Debounce Interval (s)",
        json_schema_extra={"widget": "Spinner", "advanced": True},
    )

    @field_validator("connectionmaxretries")
    def validate_retries(cls, value):
        if value < 1:
            raise ValueError("connectionmaxretries must be at least 1")
        return value

    @field_validator("displayloglevel")
    def validate_loglevel(cls, value: LogLevel):
        """Validate that the log level is one of the defined log levels."""
        if value not in LogLevel:
            raise ValueError(f"displayloglevel must be one of {list(LogLevel)}")
        return value
