"""
Amazon Bedrock Nova Pro client for meeting scheduling agent.
"""

import json
import time
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

import boto3
from botocore.exceptions import ClientError, BotoCoreError
from botocore.config import Config

logger = logging.getLogger(__name__)


@dataclass
class TokenUsage:
    """Token usage tracking for cost estimation."""
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost_usd: float


@dataclass
class BedrockResponse:
    """Response from Bedrock API with metadata."""
    content: str
    token_usage: TokenUsage
    model_id: str
    timestamp: datetime


class BedrockClientError(Exception):
    """Custom exception for Bedrock client errors."""
    pass


class BedrockClient:
    """Amazon Bedrock client for Amazon Nova Pro model."""
    
    MODEL_ID = "amazon.nova-pro-v1:0"
    INPUT_TOKEN_COST_PER_1K = 0.0008
    OUTPUT_TOKEN_COST_PER_1K = 0.0032
    
    def __init__(self, region_name: str = "us-east-1", max_retries: int = 3):
        self.region_name = region_name
        self.max_retries = max_retries
        
        config = Config(
            region_name=region_name,
            retries={'max_attempts': max_retries, 'mode': 'adaptive'}
        )
        
        try:
            self.client = boto3.client('bedrock-runtime', config=config)
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {e}")
            raise BedrockClientError(f"Failed to initialize Bedrock client: {e}")
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate estimated cost based on token usage."""
        input_cost = (input_tokens / 1000) * self.INPUT_TOKEN_COST_PER_1K
        output_cost = (output_tokens / 1000) * self.OUTPUT_TOKEN_COST_PER_1K
        return input_cost + output_cost
    
    def _parse_response(self, response: Dict[str, Any]) -> BedrockResponse:
        """Parse Bedrock API response and extract token usage."""
        try:
            response_body = json.loads(response['body'].read())
            content = response_body['content'][0]['text']
            
            usage = response_body['usage']
            input_tokens = usage['input_tokens']
            output_tokens = usage['output_tokens']
            total_tokens = input_tokens + output_tokens
            
            estimated_cost = self._calculate_cost(input_tokens, output_tokens)
            
            token_usage = TokenUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                estimated_cost_usd=estimated_cost
            )
            
            return BedrockResponse(
                content=content,
                token_usage=token_usage,
                model_id=self.MODEL_ID,
                timestamp=datetime.utcnow()
            )
            
        except (KeyError, json.JSONDecodeError, IndexError) as e:
            logger.error(f"Failed to parse Bedrock response: {e}")
            raise BedrockClientError(f"Failed to parse Bedrock response: {e}")
    
    def _invoke_with_retry(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke Bedrock API with retry logic."""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.invoke_model(
                    modelId=self.MODEL_ID,
                    body=json.dumps(body),
                    contentType='application/json',
                    accept='application/json'
                )
                
                logger.info(f"Bedrock API call successful on attempt {attempt + 1}")
                return response
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                last_exception = e
                
                if error_code in ['ThrottlingException', 'ServiceUnavailableException']:
                    if attempt < self.max_retries:
                        wait_time = (2 ** attempt) + (0.1 * attempt)
                        logger.warning(f"Bedrock API throttled, retrying in {wait_time}s")
                        time.sleep(wait_time)
                        continue
                
                logger.error(f"Bedrock API error: {error_code} - {e}")
                raise BedrockClientError(f"Bedrock API error: {error_code} - {e}")
                
            except BotoCoreError as e:
                last_exception = e
                if attempt < self.max_retries:
                    wait_time = (2 ** attempt) + (0.1 * attempt)
                    logger.warning(f"Bedrock connection error, retrying in {wait_time}s")
                    time.sleep(wait_time)
                    continue
                
                logger.error(f"Bedrock connection error: {e}")
                raise BedrockClientError(f"Bedrock connection error: {e}")
        
        raise BedrockClientError(f"All retry attempts failed. Last error: {last_exception}")
    
    def invoke_model(
        self,
        prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.1,
        top_p: float = 0.9
    ) -> BedrockResponse:
        """Invoke Amazon Nova Pro model with the given prompt."""
        if not prompt or not prompt.strip():
            raise BedrockClientError("Prompt cannot be empty")
        
        body = {
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        logger.info(f"Invoking Bedrock model with {len(prompt)} character prompt")
        
        try:
            response = self._invoke_with_retry(body)
            parsed_response = self._parse_response(response)
            
            logger.info(
                f"Bedrock response: {parsed_response.token_usage.total_tokens} tokens, "
                f"${parsed_response.token_usage.estimated_cost_usd:.4f} cost"
            )
            
            return parsed_response
            
        except Exception as e:
            logger.error(f"Failed to invoke Bedrock model: {e}")
            raise