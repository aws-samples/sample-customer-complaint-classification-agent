"""Property-based tests for configuration override via environment.

Feature: agentcore-deployment, Property 6: Configuration Override via Environment
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
    COMPLAINT_CRITERIA_ENV_VAR,
)


class TestConfigurationOverrideViaEnvironment:
    """
    Feature: agentcore-deployment, Property 6: Configuration Override via Environment
    
    *For any* valid file path set in the COMPLAINT_CRITERIA_PATH environment variable,
    the configuration system SHALL load complaint criteria from that path instead of
    the default bundled config file.
    
    **Validates: Requirements 8.2**
    """

    @settings(max_examples=10)
    @given(
        keywords=st.lists(st.text(min_size=1, max_size=30), min_size=1, max_size=5),
        sentiment_indicators=st.lists(st.text(min_size=1, max_size=30), min_size=1, max_size=5),
        severity_thresholds=st.dictionaries(
            keys=st.sampled_from(["low", "medium", "high", "critical"]),
            values=st.integers(min_value=1, max_value=10),
            min_size=1,
            max_size=4
        )
    )
    def test_environment_override_loads_custom_config(
        self, keywords, sentiment_indicators, severity_thresholds
    ):
        """Environment variable overrides default config path."""
        config_data = {
            "keywords": keywords,
            "sentiment_indicators": sentiment_indicators,
            "severity_thresholds": severity_thresholds
        }
        
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        original_env = os.environ.get(COMPLAINT_CRITERIA_ENV_VAR)
        
        try:
            os.environ[COMPLAINT_CRITERIA_ENV_VAR] = temp_path
            
            resolved_path = get_config_path()
            assert str(resolved_path) == temp_path
            
            criteria = ConfigurationLoader.load_from_default()
            assert criteria.keywords == keywords
            assert criteria.sentiment_indicators == sentiment_indicators
            assert criteria.severity_thresholds == severity_thresholds
        finally:
            if original_env is not None:
                os.environ[COMPLAINT_CRITERIA_ENV_VAR] = original_env
            else:
                os.environ.pop(COMPLAINT_CRITERIA_ENV_VAR, None)
            Path(temp_path).unlink()

    def test_default_path_used_when_env_not_set(self):
        """Default config path used when environment variable is not set."""
        original_env = os.environ.get(COMPLAINT_CRITERIA_ENV_VAR)
        
        try:
            os.environ.pop(COMPLAINT_CRITERIA_ENV_VAR, None)
            
            resolved_path = get_config_path()
            assert resolved_path.name == "complaint_criteria.json"
            assert resolved_path.exists()
        finally:
            if original_env is not None:
                os.environ[COMPLAINT_CRITERIA_ENV_VAR] = original_env

    def test_env_path_takes_precedence_over_default(self):
        """Environment path takes precedence over default bundled config."""
        custom_config = {
            "keywords": ["custom_keyword"],
            "sentiment_indicators": ["custom_sentiment"],
            "severity_thresholds": {"custom": 99}
        }
        
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(custom_config, f)
            temp_path = f.name
        
        original_env = os.environ.get(COMPLAINT_CRITERIA_ENV_VAR)
        
        try:
            os.environ[COMPLAINT_CRITERIA_ENV_VAR] = temp_path
            
            criteria = ConfigurationLoader.load_from_default()
            
            assert criteria.keywords == ["custom_keyword"]
            assert criteria.sentiment_indicators == ["custom_sentiment"]
            assert criteria.severity_thresholds == {"custom": 99}
        finally:
            if original_env is not None:
                os.environ[COMPLAINT_CRITERIA_ENV_VAR] = original_env
            else:
                os.environ.pop(COMPLAINT_CRITERIA_ENV_VAR, None)
            Path(temp_path).unlink()
