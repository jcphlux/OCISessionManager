from typing import Any, Callable, List, Tuple

from pydantic import BaseModel
from pydantic.fields import FieldInfo


class TrackableBaseModel(BaseModel):
    _original_values: dict = {}
    _subscribers: List[Callable] = []

    def __init__(self, **data):
        super().__init__(**data)

        # Initialize the model (add field mappings and subscribe to submodels)
        self.initialize_model()

    def __setattr__(self, name, value):
        if name in self.model_fields:
            mapping = self.model_fields[name].json_schema_extra.get("mapping", name)
            current_value = getattr(self, name, None)

            if name not in self._original_values:
                # Store None as a marker for submodels instead of the full instance
                if isinstance(value, TrackableBaseModel):
                    self._original_values[name] = None
                else:
                    self._original_values[name] = current_value

            # Check if the value has changed
            if isinstance(current_value, TrackableBaseModel):
                # If it's a submodel, compare the instance itself
                if current_value is not value:
                    self._notify_subscribers(mapping, value)
            elif current_value != value:
                # For non-submodel fields, compare values directly
                self._notify_subscribers(mapping, value)

        super().__setattr__(name, value)

    def initialize_model(self, prefix=""):
        """
        Initialize the model by adding field mappings and subscribing to submodel changes.
        """
        for field_name, field_info in self.model_fields.items():
            # Build the full field path
            full_field_name = f"{prefix}.{field_name}" if prefix else field_name

            # Access or initialize extra_metadata
            extra = field_info.json_schema_extra
            if extra is None:
                extra = field_info.json_schema_extra = {}
            extra["mapping"] = full_field_name
            if "widget" not in extra:
                extra["widget"] = None

            # If the field is a submodel, recurse into it and subscribe to changes
            field_value = getattr(self, field_name, None)
            if isinstance(field_value, TrackableBaseModel):
                # Recurse into the submodel
                field_value.initialize_model(full_field_name)

                # Subscribe to changes in the submodel
                field_value.subscribe(
                    lambda sub_field, sub_value: self._notify_subscribers(sub_field, sub_value)
                )

    def has_changed(self) -> bool:
        """Check if any field or submodel has changed."""
        for field, original_value in self._original_values.items():
            current_value = getattr(self, field, None)
            if isinstance(current_value, TrackableBaseModel):
                # Dynamically check if the submodel has changed
                if current_value.has_changed():
                    return True
            elif current_value != original_value:
                return True
        return False

    def reset_changes(self):
        """Reset the tracking of changes, including submodels."""
        self._original_values.clear()
        for field_name, value in self.model_fields.items():
            field = getattr(self, field_name, None)
            if isinstance(field, TrackableBaseModel):
                field.reset_changes()

    def undo_changes(self):
        """Undo changes to the fields and submodels."""
        for field, original_value in self._original_values.items():
            current_value = getattr(self, field, None)
            if isinstance(current_value, TrackableBaseModel):
                # Dynamically undo changes in the submodel
                current_value.undo_changes()
            else:
                setattr(self, field, original_value)
        self._original_values.clear()

    def subscribe(self, callback: Callable[[str, Any], None]):
        """Subscribe to change events."""
        self._subscribers.append(callback)

    def _notify_subscribers(self, mapping: str, new_value: Any):
        """Notify all subscribers of a change."""
        # mapping = self.model_fields[field_name].json_schema_extra.get(
        #     "mapping", field_name
        # )
        for subscriber in self._subscribers:
            subscriber(mapping, new_value)

    def set(self, field_name: str, value: Any):
        """Set a field value and notify subscribers."""
        tree = field_name.split(".")
        target = self
        for name in tree[:-1]:
            if hasattr(self, name):
                target = getattr(self, name)
            else:
                raise AttributeError(
                    f"Field {name} not found in {self.__class__.__name__}"
                )

        field = tree[-1]
        field_type = type(getattr(target, field, None))
        if field_type is not None:
            setattr(target, field, field_type(value))

    def get(self, field_name: str) -> Tuple[Any, FieldInfo]:
        """Get a field value."""
        tree = field_name.split(".")
        target = self
        for name in tree[:-1]:
            if hasattr(target, name):
                target = getattr(target, name)
            else:
                raise AttributeError(
                    f"Field {name} not found in {self.__class__.__name__}"
                )
        field = tree[-1]
        value = getattr(target, field, None)
        if isinstance(target, BaseModel):
            return value, target.model_fields[field]
        return value, None

    class Config:
        extra = "ignore"  # Ignore extra fields
        str_strip_whitespace = True  # Strip whitespace from strings
        validate_assignment = True  # Automatically validate fields on assignment
