"""Property-based tests for configuration validation fail-fast.

Feature: agentcore-deployment, Property 7: Configuration Validation Fail-Fast
"""

import json
import os
import tempfile
from pathlib import Path

from hypothesis import given, settings, strategies as st
import pytest

from complaints_agent.config import (
    get_config_path,
    ConfigurationLoader,
    ConfigurationError,
    validate_config,
    COMPLAINT_CRITERIA_ENV_VAR,
)


class TestConfigurationValidationFailFast:
    """
    Feature: agentcore-deployment, Property 7: Configuration Validation Fail-Fast
    
    *For any* invalid configuration file (malformed JSON, missing required fields,
    or non-existent path), the configuration system SHALL raise a ConfigurationError
    with a descriptive message before agent initialization completes.
    
    **Validates: Requirements 8.3**
    """

    @settings(max_examples=10)
    @given(
        malformed_json=st.text(min_size=1, max_size=100).filter(
            lambda x: not x.strip().startswith("{")
        )
    )
    def test_malformed_json_raises_configuration_error(self, malformed_json):
        """Malformed JSON raises ConfigurationError with descriptive message."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write(malformed_json)
            temp_path = f.name
        
        try:
            with pytest.raises(ConfigurationError) as exc_info:
                ConfigurationLoader.load_criteria(temp_path)
            
            error_msg = str(exc_info.value)
            assert "Invalid JSON" in error_msg or "must be a JSON object" in error_msg
        finally:
            Path(temp_path).unlink()

    @settings(max_examples=10)
    @given(
        missing_field=st.sampled_from(["keywords", "sentiment_indicators", "severity_thresholds"])
    )
    def test_missing_required_field_raises_configuration_error(self, missing_field):
        """Missing required fields raise ConfigurationError."""
        complete_config = {
            "keywords": ["test"],
            "sentiment_indicators": ["test"],
            "severity_thresholds": {"low": 1}
        }
        del complete_config[missing_field]
        
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(complete_config, f)
            temp_path = f.name
        
        try:
            with pytest.raises(ConfigurationError) as exc_info:
                ConfigurationLoader.load_criteria(temp_path)
            
            assert "Missing required" in str(exc_info.value)
            assert missing_field in str(exc_info.value)
        finally:
            Path(temp_path).unlink()

    @settings(max_examples=10)
    @given(
        nonexistent_path=st.text(
            alphabet="abcdefghijklmnopqrstuvwxyz0123456789_-",
            min_size=5,
            max_size=20
        )
    )
    def test_nonexistent_path_raises_configuration_error(self, nonexistent_path):
        """Non-existent config path raises ConfigurationError."""
        fake_path = f"/tmp/nonexistent_{nonexistent_path}.json"
        
        if Path(fake_path).exists():
            return
        
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigurationLoader.load_criteria(fake_path)
        
        assert "not found" in str(exc_info.value)

    def test_nonexistent_env_path_raises_configuration_error(self):
        """Non-existent path in environment variable raises ConfigurationError."""
        original_env = os.environ.get(COMPLAINT_CRITERIA_ENV_VAR)
        
        try:
            os.environ[COMPLAINT_CRITERIA_ENV_VAR] = "/nonexistent/path/config.json"
            
            with pytest.raises(ConfigurationError) as exc_info:
                get_config_path()
            
            assert "not found" in str(exc_info.value)
        finally:
            if original_env is not None:
                os.environ[COMPLAINT_CRITERIA_ENV_VAR] = original_env
            else:
                os.environ.pop(COMPLAINT_CRITERIA_ENV_VAR, None)

    @settings(max_examples=10)
    @given(
        wrong_type=st.sampled_from([
            {"keywords": "not_a_list", "sentiment_indicators": [], "severity_thresholds": {}},
            {"keywords": [], "sentiment_indicators": "not_a_list", "severity_thresholds": {}},
            {"keywords": [], "sentiment_indicators": [], "severity_thresholds": "not_a_dict"},
        ])
    )
    def test_wrong_field_type_raises_configuration_error(self, wrong_type):
        """Wrong field types raise ConfigurationError."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(wrong_type, f)
            temp_path = f.name
        
        try:
            with pytest.raises(ConfigurationError) as exc_info:
                ConfigurationLoader.load_criteria(temp_path)
            
            assert "must be" in str(exc_info.value)
        finally:
            Path(temp_path).unlink()

    def test_empty_json_object_raises_configuration_error(self):
        """Empty JSON object raises ConfigurationError for missing fields."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump({}, f)
            temp_path = f.name
        
        try:
            with pytest.raises(ConfigurationError) as exc_info:
                ConfigurationLoader.load_criteria(temp_path)
            
            assert "Missing required" in str(exc_info.value)
        finally:
            Path(temp_path).unlink()
