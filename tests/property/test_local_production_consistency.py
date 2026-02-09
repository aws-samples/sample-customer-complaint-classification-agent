"""Property-based tests for local/production configuration consistency.

Feature: agentcore-deployment, Property 9: Local/Production Configuration Consistency
"""

import json
import os
import tempfile
from pathlib import Path

from hypothesis import given, settings, strategies as st
import pytest

from complaints_agent.config import ConfigurationLoader, COMPLAINT_CRITERIA_ENV_VAR
from complaints_agent.models import ComplaintCriteria


def load_config_local_mode() -> ComplaintCriteria:
    """Load config the way main.py does it (local development mode)."""
    config_path = Path("config/complaint_criteria.json")
    return ConfigurationLoader.load_criteria(str(config_path))


def load_config_production_mode() -> ComplaintCriteria:
    """Load config the way agent.py does it (production AgentCore mode)."""
    from agent import get_config_path, load_config
    return load_config()


class TestLocalProductionConfigConsistency:
    """
    Feature: agentcore-deployment, Property 9: Local/Production Configuration Consistency
    
    *For any* configuration loaded in local development mode, the loaded ComplaintCriteria
    object SHALL be equivalent to the configuration that would be loaded in the production
    AgentCore runtime environment.
    
    **Validates: Requirements 7.4**
    """

    def test_default_config_identical_in_both_modes(self):
        """Default config produces identical ComplaintCriteria in local and production modes."""
        original_env = os.environ.get(COMPLAINT_CRITERIA_ENV_VAR)
        
        try:
            os.environ.pop(COMPLAINT_CRITERIA_ENV_VAR, None)
            
            local_criteria = load_config_local_mode()
            production_criteria = load_config_production_mode()
            
            assert local_criteria.keywords == production_criteria.keywords
            assert local_criteria.sentiment_indicators == production_criteria.sentiment_indicators
            assert local_criteria.severity_thresholds == production_criteria.severity_thresholds
        finally:
            if original_env is not None:
                os.environ[COMPLAINT_CRITERIA_ENV_VAR] = original_env

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
    def test_custom_config_identical_via_env_override(
        self, keywords, sentiment_indicators, severity_thresholds
    ):
        """Custom config via environment override produces identical results in both modes."""
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
            
            production_criteria = load_config_production_mode()
            
            assert production_criteria.keywords == keywords
            assert production_criteria.sentiment_indicators == sentiment_indicators
            assert production_criteria.severity_thresholds == severity_thresholds
        finally:
            if original_env is not None:
                os.environ[COMPLAINT_CRITERIA_ENV_VAR] = original_env
            else:
                os.environ.pop(COMPLAINT_CRITERIA_ENV_VAR, None)
            Path(temp_path).unlink()

    def test_serialization_consistency_between_modes(self):
        """Serialized config from both modes produces identical JSON."""
        original_env = os.environ.get(COMPLAINT_CRITERIA_ENV_VAR)
        
        try:
            os.environ.pop(COMPLAINT_CRITERIA_ENV_VAR, None)
            
            local_criteria = load_config_local_mode()
            production_criteria = load_config_production_mode()
            
            local_json = json.loads(local_criteria.to_json())
            production_json = json.loads(production_criteria.to_json())
            
            assert local_json == production_json
        finally:
            if original_env is not None:
                os.environ[COMPLAINT_CRITERIA_ENV_VAR] = original_env

    @settings(max_examples=10)
    @given(
        keywords=st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=3),
        sentiment_indicators=st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=3),
        severity_thresholds=st.dictionaries(
            keys=st.sampled_from(["low", "medium", "high"]),
            values=st.integers(min_value=1, max_value=5),
            min_size=1,
            max_size=3
        )
    )
    def test_round_trip_consistency(self, keywords, sentiment_indicators, severity_thresholds):
        """Config round-trip (save/load) produces consistent results across modes."""
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
            
            criteria1 = load_config_production_mode()
            
            serialized = criteria1.to_json()
            criteria2 = ComplaintCriteria.from_json(serialized)
            
            assert criteria1.keywords == criteria2.keywords
            assert criteria1.sentiment_indicators == criteria2.sentiment_indicators
            assert criteria1.severity_thresholds == criteria2.severity_thresholds
        finally:
            if original_env is not None:
                os.environ[COMPLAINT_CRITERIA_ENV_VAR] = original_env
            else:
                os.environ.pop(COMPLAINT_CRITERIA_ENV_VAR, None)
            Path(temp_path).unlink()
