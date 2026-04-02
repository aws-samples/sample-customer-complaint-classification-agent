"""Configuration loader for complaint criteria."""

import json
import os
from pathlib import Path

from complaint_system.models import ComplaintCriteria


COMPLAINT_CRITERIA_ENV_VAR = "COMPLAINT_CRITERIA_PATH"
DEFAULT_CONFIG_FILENAME = "complaint_criteria.json"


class ConfigurationError(Exception):
    """Exception raised for configuration loading errors."""
    pass


def get_config_path() -> Path:
    """Get the configuration file path with environment variable override.
    
    Checks for COMPLAINT_CRITERIA_PATH environment variable first.
    Falls back to the default bundled config file location.
    
    Returns:
        Path to the configuration file
        
    Raises:
        ConfigurationError: If the resolved path does not exist
    """
    env_path = os.environ.get(COMPLAINT_CRITERIA_ENV_VAR)
    if env_path:
        path = Path(env_path)
        if not path.exists():
            raise ConfigurationError(
                f"Configuration file not found at environment path: {env_path}"
            )
        return path
    
    default_path = Path(__file__).parent.parent.parent.parent / "config" / DEFAULT_CONFIG_FILENAME
    if not default_path.exists():
        raise ConfigurationError(
            f"Default configuration file not found: {default_path}"
        )
    return default_path


def validate_config(data: dict) -> None:
    """Validate configuration data structure.
    
    Args:
        data: Parsed configuration dictionary
        
    Raises:
        ConfigurationError: If required fields are missing or invalid
    """
    if not isinstance(data, dict):
        raise ConfigurationError("Configuration must be a JSON object")
    
    required_fields = ["keywords", "sentiment_indicators", "severity_thresholds"]
    
    for field in required_fields:
        if field not in data:
            raise ConfigurationError(f"Missing required configuration field: {field}")
    
    if not isinstance(data["keywords"], list):
        raise ConfigurationError("Field 'keywords' must be a list")
    
    if not isinstance(data["sentiment_indicators"], list):
        raise ConfigurationError("Field 'sentiment_indicators' must be a list")
    
    if not isinstance(data["severity_thresholds"], dict):
        raise ConfigurationError("Field 'severity_thresholds' must be a dictionary")


class ConfigurationLoader:
    """Loads complaint criteria from configuration sources."""

    @staticmethod
    def load_criteria(config_path: str) -> ComplaintCriteria:
        """Load complaint criteria from JSON configuration file.

        Args:
            config_path: Path to the configuration file

        Returns:
            ComplaintCriteria object

        Raises:
            ConfigurationError: If file not found, JSON parse error, or validation fails
        """
        path = Path(config_path)
        
        if not path.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            data = json.loads(content)
            validate_config(data)
            return ComplaintCriteria.from_json(content)
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in configuration file: {e}")
    
    @staticmethod
    def load_from_default() -> ComplaintCriteria:
        """Load complaint criteria from the default or environment-configured path.
        
        Returns:
            ComplaintCriteria object
            
        Raises:
            ConfigurationError: If configuration cannot be loaded or is invalid
        """
        config_path = get_config_path()
        return ConfigurationLoader.load_criteria(str(config_path))

    @staticmethod
    def serialize_criteria(criteria: ComplaintCriteria) -> str:
        """Serialize complaint criteria to JSON string.

        Args:
            criteria: ComplaintCriteria object

        Returns:
            JSON string representation
        """
        return criteria.to_json()

    @staticmethod
    def deserialize_criteria(json_str: str) -> ComplaintCriteria:
        """Deserialize JSON string to ComplaintCriteria object.

        Args:
            json_str: JSON string representation

        Returns:
            ComplaintCriteria object

        Raises:
            ConfigurationError: If JSON parse error
        """
        try:
            return ComplaintCriteria.from_json(json_str)
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON string: {e}")
