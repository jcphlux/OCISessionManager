from typing import Optional

from pydantic import Field

from ocisessionmanager.models.trackable_base_model import TrackableBaseModel


class ConnectionSettings(TrackableBaseModel):
    localport: int = Field(
        32222,
        description="Local port for connections",
        title="Local Port",
        multiple_of=1,
        gt=-1,
        lt=65536,
        json_schema_extra={"widget": "Spinner", "advanced": False},
    )
    targetport: int = Field(
        22,
        description="Target port for connections",
        title="Target Port",
        multiple_of=1,
        gt=-1,
        lt=65536,
        json_schema_extra={"widget": "Spinner", "advanced": False},
    )
    tenancyoverride: Optional[str] = Field(
        None,
        description="Override for tenancy",
        title="Tenancy Override",
        json_schema_extra={"widget": "Text", "advanced": False},
    )
    sessionlength: int = Field(
        10800,
        description="Session TTL in seconds",
        title="Session TTL (s)",
        multiple_of=1,
        gt=300,
        lt=28800,
        json_schema_extra={"widget": "Spinner", "advanced": False},
    )
