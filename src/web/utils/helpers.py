import boto3
import json
import os
import logging
from dataclasses import dataclass

@dataclass
class Prompts:
    user_prompt: str
    system_prompt: str

@dataclass
class ModelSettings:
    temperature: float
    max_tokens: int
    top_p: float
    model_id: str

def bedrock_init():
    """
    NOTE: This method uses existing AWS credentials. This could be the IAM instance profile, pod identity, etc.
    It just depends on the platform you're running on.

    :return: Bedrock AWS SDK Control Plane and Runtime Clients
    """
    try:
        bedrock_runtime_client = boto3.client("bedrock-runtime")
        bedrock_service_client = boto3.client("bedrock")
        return bedrock_runtime_client, bedrock_service_client
    except Exception as e:
        print(f"Unable to initialize Amazon Bedrock Client(s): {str(e)}")

def list_foundation_models(service_client):
    """
    List the foundation models available for use. Filter out models that don't output text.
    :param service_client:
    :return: List[str]
    """
    try:
        models_list = []

        response = service_client.list_foundation_models()
        models = response["modelSummaries"]
        for model in models:
            if "TEXT" in model["inputModalities"] and "TEXT" in model["outputModalities"]:
                if len(model["modelId"].split(":")) < 3:
                    models_list.append(model["modelId"])
        return models_list
    except Exception as e:
        print(f"Error listing models: {str(e)}")
        raise e

def converse(prompts: Prompts, model_settings: ModelSettings, runtime_client):
    """
    User invokes analysis which uses model details and prompts input by the user. Returns both the response and
    usage details.
    :param prompts: A class which describes both the user and system prompts
    :param model_settings: A class which describes the model settings (temp, top P, max tokens, etc.)
    :param runtime_client: The AWS SDK client for Amazon Bedrock runtime
    :return: Response from model and usage details
    """
    _messages = [
        {
            "role": "user",
            "content": [
                {
                    "text": prompts.user_prompt
                }
            ]
        }
    ]
    try:
        _response = runtime_client.converse(
            system = [
                {
                    "text": prompts.system_prompt
                }
            ],
            inferenceConfig = {
                "maxTokens": model_settings.max_tokens,
                "temperature": model_settings.temperature,
                "topP": model_settings.top_p
            },
            modelId = model_settings.model_id,
            messages = _messages
        )

        _response_text = _response["output"]["message"]["content"][0]["text"]
        _usage = _response["usage"]
        return _response_text, _usage
    except Exception as e:
        print(f"Error when conversing with {model_settings.model_id}: {str(e)}")

