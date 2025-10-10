"""
Tests for Bedrock client functionality.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.services.bedrock_client import (
    BedrockClient, 
    BedrockResponse, 
    TokenUsage, 
    BedrockClientError
)


class TestBedrockClient:
    """Test cases for BedrockClient."""
    
    def test_init_success(self):
        """Test successful client initialization."""
        with patch('boto3.client') as mock_boto3:
            mock_boto3.return_value = Mock()
            client = BedrockClient()
            
            assert client.region_name == "us-east-1"
            assert client.max_retries == 3
            assert client.MODEL_ID == "amazon.nova-pro-v1:0"
    
    def test_init_failure(self):
        """Test client initialization failure."""
        with patch('boto3.client', side_effect=Exception("AWS error")):
            with pytest.raises(BedrockClientError):
                BedrockClient()
    
    def test_calculate_cost(self):
        """Test cost calculation."""
        with patch('boto3.client'):
            client = BedrockClient()
            
            # Test with 1000 input tokens and 500 output tokens
            cost = client._calculate_cost(1000, 500)
            expected_cost = (1000/1000 * 0.003) + (500/1000 * 0.015)
            assert cost == expected_cost
    
    def test_parse_response_success(self):
        """Test successful response parsing."""
        with patch('boto3.client'):
            client = BedrockClient()
            
            # Mock response
            mock_response = {
                'body': Mock()
            }
            
            response_data = {
                'content': [{'text': 'Test response'}],
                'usage': {
                    'input_tokens': 100,
                    'output_tokens': 50
                }
            }
            
            mock_response['body'].read.return_value = json.dumps(response_data)
            
            result = client._parse_response(mock_response)
            
            assert isinstance(result, BedrockResponse)
            assert result.content == 'Test response'
            assert result.token_usage.input_tokens == 100
            assert result.token_usage.output_tokens == 50
            assert result.token_usage.total_tokens == 150
    
    def test_parse_response_failure(self):
        """Test response parsing failure."""
        with patch('boto3.client'):
            client = BedrockClient()
            
            # Mock invalid response
            mock_response = {
                'body': Mock()
            }
            mock_response['body'].read.return_value = "invalid json"
            
            with pytest.raises(BedrockClientError):
                client._parse_response(mock_response)
    
    def test_invoke_model_success(self):
        """Test successful model invocation."""
        with patch('boto3.client') as mock_boto3:
            mock_client = Mock()
            mock_boto3.return_value = mock_client
            
            # Mock successful response
            mock_response = {
                'body': Mock()
            }
            
            response_data = {
                'content': [{'text': 'AI response'}],
                'usage': {
                    'input_tokens': 50,
                    'output_tokens': 25
                }
            }
            
            mock_response['body'].read.return_value = json.dumps(response_data)
            mock_client.invoke_model.return_value = mock_response
            
            client = BedrockClient()
            result = client.invoke_model("Test prompt")
            
            assert isinstance(result, BedrockResponse)
            assert result.content == 'AI response'
            assert result.token_usage.input_tokens == 50
            assert result.token_usage.output_tokens == 25
    
    def test_invoke_model_empty_prompt(self):
        """Test model invocation with empty prompt."""
        with patch('boto3.client'):
            client = BedrockClient()
            
            with pytest.raises(BedrockClientError, match="Prompt cannot be empty"):
                client.invoke_model("")
    
    def test_invoke_with_retry_throttling(self):
        """Test retry logic with throttling."""
        with patch('boto3.client') as mock_boto3:
            mock_client = Mock()
            mock_boto3.return_value = mock_client
            
            # First call fails with throttling, second succeeds
            from botocore.exceptions import ClientError
            
            throttle_error = ClientError(
                {'Error': {'Code': 'ThrottlingException'}}, 
                'invoke_model'
            )
            
            mock_response = {
                'body': Mock()
            }
            response_data = {
                'content': [{'text': 'Success'}],
                'usage': {'input_tokens': 10, 'output_tokens': 5}
            }
            mock_response['body'].read.return_value = json.dumps(response_data)
            
            mock_client.invoke_model.side_effect = [throttle_error, mock_response]
            
            client = BedrockClient(max_retries=2)
            
            with patch('time.sleep'):  # Mock sleep to speed up test
                result = client.invoke_model("Test prompt")
                
            assert result.content == 'Success'
            assert mock_client.invoke_model.call_count == 2


class TestTokenUsage:
    """Test cases for TokenUsage dataclass."""
    
    def test_token_usage_creation(self):
        """Test TokenUsage creation."""
        usage = TokenUsage(
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            estimated_cost_usd=0.0045
        )
        
        assert usage.input_tokens == 100
        assert usage.output_tokens == 50
        assert usage.total_tokens == 150
        assert usage.estimated_cost_usd == 0.0045


class TestBedrockResponse:
    """Test cases for BedrockResponse dataclass."""
    
    def test_bedrock_response_creation(self):
        """Test BedrockResponse creation."""
        usage = TokenUsage(100, 50, 150, 0.0045)
        timestamp = datetime.utcnow()
        
        response = BedrockResponse(
            content="Test content",
            token_usage=usage,
            model_id="test-model",
            timestamp=timestamp
        )
        
        assert response.content == "Test content"
        assert response.token_usage == usage
        assert response.model_id == "test-model"
        assert response.timestamp == timestamp