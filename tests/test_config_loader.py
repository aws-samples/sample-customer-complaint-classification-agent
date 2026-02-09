"""Unit tests for ConfigurationLoader."""

import json
import tempfile
from pathlib import Path

import pytest

from complaints_agent.config import ConfigurationLoader, ConfigurationError
from complaints_agent.models import ComplaintCriteria


class TestConfigurationLoader:
    """Unit tests for configuration loading functionality."""

    def test_load_criteria_from_valid_json_file(self):
        """Test loading criteria from a valid JSON configuration file.
        
        _Requirements: 2.1_
        """
        criteria_data = {
            "keywords": ["complaint", "unhappy", "frustrated"],
            "sentiment_indicators": ["terrible service", "very disappointed"],
            "severity_thresholds": {"low": 1, "medium": 3, "high": 5}
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(criteria_data, f)
            temp_path = f.name
        
        try:
            criteria = ConfigurationLoader.load_criteria(temp_path)
            
            assert criteria.keywords == ["complaint", "unhappy", "frustrated"]
            assert criteria.sentiment_indicators == ["terrible service", "very disappointed"]
            assert criteria.severity_thresholds == {"low": 1, "medium": 3, "high": 5}
        finally:
            Path(temp_path).unlink()

    def test_load_criteria_file_not_found(self):
        """Test error handling when configuration file does not exist.
        
        _Requirements: 2.1_
        """
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigurationLoader.load_criteria("/nonexistent/path/config.json")
        
        assert "Configuration file not found" in str(exc_info.value)

    def test_load_criteria_invalid_json(self):
        """Test error handling for invalid JSON in configuration file.
        
        _Requirements: 2.1_
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{ invalid json }")
            temp_path = f.name
        
        try:
            with pytest.raises(ConfigurationError) as exc_info:
                ConfigurationLoader.load_criteria(temp_path)
            
            assert "Invalid JSON" in str(exc_info.value)
        finally:
            Path(temp_path).unlink()

    def test_serialize_criteria(self):
        """Test serializing ComplaintCriteria to JSON string."""
        criteria = ComplaintCriteria(
            keywords=["issue", "problem"],
            sentiment_indicators=["not happy"],
            severity_thresholds={"low": 1}
        )
        
        json_str = ConfigurationLoader.serialize_criteria(criteria)
        data = json.loads(json_str)
        
        assert data["keywords"] == ["issue", "problem"]
        assert data["sentiment_indicators"] == ["not happy"]
        assert data["severity_thresholds"] == {"low": 1}

    def test_deserialize_criteria(self):
        """Test deserializing JSON string to ComplaintCriteria."""
        json_str = json.dumps({
            "keywords": ["complaint"],
            "sentiment_indicators": ["upset"],
            "severity_thresholds": {"high": 10}
        })
        
        criteria = ConfigurationLoader.deserialize_criteria(json_str)
        
        assert criteria.keywords == ["complaint"]
        assert criteria.sentiment_indicators == ["upset"]
        assert criteria.severity_thresholds == {"high": 10}

    def test_deserialize_criteria_invalid_json(self):
        """Test error handling for invalid JSON string during deserialization."""
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigurationLoader.deserialize_criteria("not valid json")
        
        assert "Invalid JSON string" in str(exc_info.value)
