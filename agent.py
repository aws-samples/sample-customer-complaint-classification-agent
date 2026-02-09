"""AgentCore Entry Point Wrapper for Complaints Agent."""

import json
import os
import sys
from pathlib import Path

src_path = Path(__file__).parent / "src"
if src_path.exists() and str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from bedrock_agentcore import BedrockAgentCoreApp

from complaints_agent.agents import SupervisorAgent
from complaints_agent.config import ConfigurationLoader
from complaints_agent.config.loader import ConfigurationError


def get_config_path() -> Path:
    env_path = os.environ.get("COMPLAINT_CRITERIA_PATH")
    if env_path:
        return Path(env_path)
    return Path(__file__).parent / "config" / "complaint_criteria.json"


def load_config():
    config_path = get_config_path()
    if not config_path.exists():
        raise ConfigurationError(f"Configuration file not found: {config_path}")
    return ConfigurationLoader.load_criteria(str(config_path))


def apply_config_override(base_criteria, config_override: dict):
    from complaints_agent.models import ComplaintCriteria
    
    keywords = config_override.get("keywords", base_criteria.keywords)
    sentiment_indicators = config_override.get("sentiment_indicators", base_criteria.sentiment_indicators)
    severity_thresholds = config_override.get("severity_thresholds", base_criteria.severity_thresholds)
    
    return ComplaintCriteria(
        keywords=keywords if isinstance(keywords, list) else base_criteria.keywords,
        sentiment_indicators=sentiment_indicators if isinstance(sentiment_indicators, list) else base_criteria.sentiment_indicators,
        severity_thresholds=severity_thresholds if isinstance(severity_thresholds, dict) else base_criteria.severity_thresholds
    )


app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload: dict, context: dict) -> dict:
    try:
        transcript = payload.get("transcript")
        
        if transcript is None:
            return {"status": "error", "error_message": "Missing required field: transcript"}
        
        if not isinstance(transcript, str):
            return {"status": "error", "error_message": "Invalid transcript: must be a string"}
        
        if not transcript.strip():
            return {"status": "error", "error_message": "Transcript cannot be empty"}
        
        try:
            criteria = load_config()
        except ConfigurationError as e:
            return {"status": "error", "error_message": f"Failed to load configuration: {str(e)}"}
        
        config_override = payload.get("config_override")
        if config_override is not None:
            if not isinstance(config_override, dict):
                return {"status": "error", "error_message": "Invalid config_override: must be an object"}
            criteria = apply_config_override(criteria, config_override)
        
        supervisor = SupervisorAgent(criteria)
        response = supervisor.process_transcript(transcript)
        
        return {"result": json.loads(response.to_json())}
        
    except Exception as e:
        return {"status": "error", "error_message": f"Agent processing failed: {str(e)}"}


if __name__ == "__main__":
    app.run()
