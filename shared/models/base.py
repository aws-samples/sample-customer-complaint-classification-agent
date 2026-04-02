from dataclasses import fields
from datetime import datetime
from typing import TypeVar, get_type_hints, get_origin, get_args, Union
import json

T = TypeVar('T', bound='Serializable')


class Serializable:
    """Mixin providing JSON serialization for dataclasses."""

    def to_dict(self) -> dict:
        """Convert to a plain dictionary."""
        def serialize_value(val):
            if val is None:
                return None
            if isinstance(val, datetime):
                return val.isoformat()
            if isinstance(val, Serializable):
                return val.to_dict()
            if isinstance(val, list):
                return [serialize_value(item) for item in val]
            if isinstance(val, dict):
                return {k: serialize_value(v) for k, v in val.items()}
            return val

        data = {}
        for field in fields(self):
            val = getattr(self, field.name)
            data[field.name] = serialize_value(val)
        return data

    def to_json(self) -> str:
        """Serialize to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls: type[T], json_str: str) -> T:
        """Deserialize from a JSON string."""
        data = json.loads(json_str)
        hints = get_type_hints(cls)
        kwargs = {}

        for field in fields(cls):
            val = data.get(field.name)
            field_type = hints.get(field.name)

            if val is not None:
                val = cls._deserialize_value(val, field_type)

            kwargs[field.name] = val

        return cls(**kwargs)

    @classmethod
    def _deserialize_value(cls, val, field_type):
        if val is None:
            return None

        actual_type = cls._unwrap_optional(field_type)

        if actual_type == datetime:
            return datetime.fromisoformat(val)

        if hasattr(actual_type, 'from_json') and isinstance(val, dict):
            return actual_type.from_json(json.dumps(val))

        return val

    @staticmethod
    def _unwrap_optional(field_type):
        origin = get_origin(field_type)
        if origin is Union:
            args = get_args(field_type)
            non_none_args = [arg for arg in args if arg is not type(None)]
            if len(non_none_args) == 1:
                return non_none_args[0]
        return field_type
