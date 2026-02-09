import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional

from src.complaints_agent.models.base import Serializable


@dataclass
class SimpleModel(Serializable):
    name: str
    value: int


@dataclass
class ModelWithDatetime(Serializable):
    transcript: str
    timestamp: datetime
    items: List[str] = field(default_factory=list)


@dataclass
class ModelWithDict(Serializable):
    keywords: List[str] = field(default_factory=list)
    thresholds: Dict[str, int] = field(default_factory=dict)


@dataclass
class NestedModel(Serializable):
    is_valid: bool
    summary: str
    inner: Optional[SimpleModel] = None
    inner_with_datetime: Optional[ModelWithDatetime] = None


class TestSerializableToJson:
    def test_simple_model_serialization(self):
        model = SimpleModel(name="test", value=42)
        json_str = model.to_json()
        data = json.loads(json_str)

        assert data["name"] == "test"
        assert data["value"] == 42

    def test_datetime_serialization(self):
        timestamp = datetime(2024, 1, 15, 10, 30, 0)
        model = ModelWithDatetime(
            transcript="Hello",
            timestamp=timestamp,
            items=["a", "b"]
        )
        json_str = model.to_json()
        data = json.loads(json_str)

        assert data["transcript"] == "Hello"
        assert data["timestamp"] == "2024-01-15T10:30:00"
        assert data["items"] == ["a", "b"]

    def test_dict_serialization(self):
        model = ModelWithDict(
            keywords=["error", "problem"],
            thresholds={"low": 1, "high": 5}
        )
        json_str = model.to_json()
        data = json.loads(json_str)

        assert data["keywords"] == ["error", "problem"]
        assert data["thresholds"] == {"low": 1, "high": 5}

    def test_nested_model_serialization(self):
        inner = SimpleModel(name="inner", value=10)
        model = NestedModel(is_valid=True, summary="test", inner=inner)
        json_str = model.to_json()
        data = json.loads(json_str)

        assert data["is_valid"] is True
        assert data["summary"] == "test"
        assert data["inner"]["name"] == "inner"
        assert data["inner"]["value"] == 10

    def test_none_nested_model_serialization(self):
        model = NestedModel(is_valid=False, summary="empty")
        json_str = model.to_json()
        data = json.loads(json_str)

        assert data["is_valid"] is False
        assert data["summary"] == "empty"
        assert data["inner"] is None


class TestSerializableFromJson:
    def test_simple_model_deserialization(self):
        json_str = '{"name": "test", "value": 42}'
        model = SimpleModel.from_json(json_str)

        assert model.name == "test"
        assert model.value == 42

    def test_datetime_deserialization(self):
        json_str = '{"transcript": "Hello", "timestamp": "2024-01-15T10:30:00", "items": ["a", "b"]}'
        model = ModelWithDatetime.from_json(json_str)

        assert model.transcript == "Hello"
        assert model.timestamp == datetime(2024, 1, 15, 10, 30, 0)
        assert model.items == ["a", "b"]

    def test_dict_deserialization(self):
        json_str = '{"keywords": ["error", "problem"], "thresholds": {"low": 1, "high": 5}}'
        model = ModelWithDict.from_json(json_str)

        assert model.keywords == ["error", "problem"]
        assert model.thresholds == {"low": 1, "high": 5}

    def test_nested_model_deserialization(self):
        json_str = '{"is_valid": true, "summary": "test", "inner": {"name": "inner", "value": 10}, "inner_with_datetime": null}'
        model = NestedModel.from_json(json_str)

        assert model.is_valid is True
        assert model.summary == "test"
        assert model.inner is not None
        assert model.inner.name == "inner"
        assert model.inner.value == 10

    def test_none_nested_model_deserialization(self):
        json_str = '{"is_valid": false, "summary": "empty", "inner": null, "inner_with_datetime": null}'
        model = NestedModel.from_json(json_str)

        assert model.is_valid is False
        assert model.summary == "empty"
        assert model.inner is None


class TestSerializableRoundTrip:
    def test_simple_model_round_trip(self):
        original = SimpleModel(name="test", value=42)
        json_str = original.to_json()
        restored = SimpleModel.from_json(json_str)

        assert restored.name == original.name
        assert restored.value == original.value

    def test_datetime_model_round_trip(self):
        original = ModelWithDatetime(
            transcript="Hello world",
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            items=["a", "b", "c"]
        )
        json_str = original.to_json()
        restored = ModelWithDatetime.from_json(json_str)

        assert restored.transcript == original.transcript
        assert restored.timestamp == original.timestamp
        assert restored.items == original.items

    def test_nested_model_round_trip(self):
        inner = SimpleModel(name="inner", value=10)
        original = NestedModel(is_valid=True, summary="test", inner=inner)
        json_str = original.to_json()
        restored = NestedModel.from_json(json_str)

        assert restored.is_valid == original.is_valid
        assert restored.summary == original.summary
        assert restored.inner is not None
        assert restored.inner.name == original.inner.name
        assert restored.inner.value == original.inner.value

    def test_complex_nested_round_trip(self):
        inner_datetime = ModelWithDatetime(
            transcript="nested",
            timestamp=datetime(2024, 6, 1, 12, 0, 0),
            items=["x", "y"]
        )
        original = NestedModel(
            is_valid=True,
            summary="complex",
            inner=None,
            inner_with_datetime=inner_datetime
        )
        json_str = original.to_json()
        restored = NestedModel.from_json(json_str)

        assert restored.is_valid == original.is_valid
        assert restored.summary == original.summary
        assert restored.inner is None
        assert restored.inner_with_datetime is not None
        assert restored.inner_with_datetime.transcript == inner_datetime.transcript
        assert restored.inner_with_datetime.timestamp == inner_datetime.timestamp
        assert restored.inner_with_datetime.items == inner_datetime.items
