"""
Configuration settings for Amazon Bedrock client.
"""

import os
from typing import Dict, Any


class BedrockConfig:
    """Configuration class for Bedrock client settings."""
    
    # Default AWS region for Bedrock
    DEFAULT_REGION = "eu-west-1"
    
    # Model configuration - using inference profile for Nova Pro
    MODEL_ID = "eu.amazon.nova-pro-v1:0"
    
    # Default parameters
    DEFAULT_MAX_TOKENS = 4096
    DEFAULT_TEMPERATURE = 0.1
    DEFAULT_TOP_P = 0.9
    DEFAULT_MAX_RETRIES = 3
    
    # Cost tracking (per 1K tokens) - Amazon Nova Pro pricing
    INPUT_TOKEN_COST_PER_1K = 0.0008  # $0.0008 per 1K input tokens
    OUTPUT_TOKEN_COST_PER_1K = 0.0032  # $0.0032 per 1K output tokens
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """
        Get Bedrock configuration from environment variables or defaults.
        
        Returns:
            Dictionary containing Bedrock configuration
        """
        return {
            'region_name': os.getenv('AWS_BEDROCK_REGION', cls.DEFAULT_REGION),
            'model_id': os.getenv('AWS_BEDROCK_MODEL_ID', cls.MODEL_ID),
            'max_tokens': int(os.getenv('AWS_BEDROCK_MAX_TOKENS', cls.DEFAULT_MAX_TOKENS)),
            'temperature': float(os.getenv('AWS_BEDROCK_TEMPERATURE', cls.DEFAULT_TEMPERATURE)),
            'top_p': float(os.getenv('AWS_BEDROCK_TOP_P', cls.DEFAULT_TOP_P)),
            'max_retries': int(os.getenv('AWS_BEDROCK_MAX_RETRIES', cls.DEFAULT_MAX_RETRIES)),
            'input_token_cost_per_1k': float(os.getenv('AWS_BEDROCK_INPUT_COST', cls.INPUT_TOKEN_COST_PER_1K)),
            'output_token_cost_per_1k': float(os.getenv('AWS_BEDROCK_OUTPUT_COST', cls.OUTPUT_TOKEN_COST_PER_1K))
        }
    
    @classmethod
    def get_client_config(cls) -> Dict[str, Any]:
        """
        Get configuration specifically for BedrockClient initialization.
        
        Returns:
            Dictionary containing client configuration
        """
        config = cls.get_config()
        return {
            'region_name': config['region_name'],
            'max_retries': config['max_retries']
        }
    
    @classmethod
    def get_model_params(cls) -> Dict[str, Any]:
        """
        Get default model parameters for inference.
        
        Returns:
            Dictionary containing model parameters
        """
        config = cls.get_config()
        return {
            'max_tokens': config['max_tokens'],
            'temperature': config['temperature'],
            'top_p': config['top_p']
        }