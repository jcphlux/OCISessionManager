from typing import Any, Optional

from pydantic import (
    Field,
    FilePath,
    ValidationInfo,
    ValidatorFunctionWrapHandler,
    field_validator,
)

from ocisessionmanager.models.trackable_base_model import TrackableBaseModel


class KeyPaths(TrackableBaseModel):
    privkeypath: Optional[FilePath] = Field(
        "",
        description="Path to the private key file",
        title="Private Key Path",
        json_schema_extra={"widget": "File", "advanced": False},
    )
    pubkeypath: Optional[FilePath] = Field(
        "",
        description="Path to the public key file",
        title="Public Key Path",
        json_schema_extra={"widget": "File", "advanced": False},
    )

    @field_validator("*", mode="wrap")
    @classmethod
    def valid_path(
        cls,
        value: FilePath,
        handler: ValidatorFunctionWrapHandler,
        info: ValidationInfo,
    ) -> Any:
        """Validate that the path exists."""

        if not info.data or not info.data.get(info.field_name, None):
            return value

        results = handler(value)

        if results and not results.exists():
            raise ValueError(f"Path {results} does not exist.")
        return results
