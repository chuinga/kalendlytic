"""
Kalendlytic AWS service client utilities with proper configuration and error handling.
"""

import boto3
from botocore.config import Config
from typing import Optional


def get_boto3_config() -> Config:
    """Get standardized boto3 configuration."""
    return Config(
        region_name='eu-west-1',  # TODO: Make configurable via environment
        retries={
            'max_attempts': 3,
            'mode': 'adaptive'
        },
        max_pool_connections=50
    )


def get_dynamodb_client():
    """Get DynamoDB client with proper configuration."""
    return boto3.client('dynamodb', config=get_boto3_config())


def get_dynamodb_resource():
    """Get DynamoDB resource with proper configuration."""
    return boto3.resource('dynamodb', config=get_boto3_config())


def get_secrets_client():
    """Get Secrets Manager client with proper configuration."""
    return boto3.client('secretsmanager', config=get_boto3_config())


def get_kms_client():
    """Get KMS client with proper configuration."""
    return boto3.client('kms', config=get_boto3_config())


def get_bedrock_client():
    """Get Bedrock client with proper configuration."""
    return boto3.client('bedrock-runtime', config=get_boto3_config())


def get_bedrock_agent_client():
    """Get Bedrock Agent client with proper configuration."""
    return boto3.client('bedrock-agent-runtime', config=get_boto3_config())