#!/usr/bin/env python3
"""
Simple test script to verify Amazon Nova Pro integration without complex imports.
"""

import boto3
import json
from botocore.config import Config

def test_nova_pro_direct():
    """Test Nova Pro directly with boto3."""
    print("=== Testing Amazon Nova Pro Direct Integration ===")
    
    # Configuration
    region = "eu-west-1"
    model_id = "eu.amazon.nova-pro-v1:0"  # Use inference profile instead of direct model
    
    print(f"Model ID: {model_id}")
    print(f"Region: {region}")
    
    try:
        # Create Bedrock client
        config = Config(
            region_name=region,
            retries={'max_attempts': 3, 'mode': 'adaptive'},
            read_timeout=60,
            connect_timeout=60
        )
        
        bedrock_client = boto3.client('bedrock-runtime', config=config)
        print("✓ Bedrock client initialized successfully")
        
        # Test a simple prompt
        print("\n=== Testing Nova Pro API Call ===")
        prompt = "Hello! Please respond with a brief greeting and confirm you are Amazon Nova Pro."
        
        # Prepare the request
        request_body = {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt}]
                }
            ],
            "inferenceConfig": {
                "maxTokens": 100,
                "temperature": 0.7
            }
        }
        
        # Make the API call
        response = bedrock_client.converse(
            modelId=model_id,
            messages=request_body["messages"],
            inferenceConfig=request_body["inferenceConfig"]
        )
        
        # Extract response
        output_message = response['output']['message']
        content = output_message['content'][0]['text']
        
        # Extract usage metrics
        usage = response.get('usage', {})
        input_tokens = usage.get('inputTokens', 0)
        output_tokens = usage.get('outputTokens', 0)
        total_tokens = usage.get('totalTokens', 0)
        
        # Calculate cost (approximate)
        input_cost_per_1k = 0.0008  # $0.0008 per 1K input tokens
        output_cost_per_1k = 0.0032  # $0.0032 per 1K output tokens
        
        input_cost = (input_tokens / 1000) * input_cost_per_1k
        output_cost = (output_tokens / 1000) * output_cost_per_1k
        total_cost = input_cost + output_cost
        
        print(f"✓ API call successful!")
        print(f"Response: {content}")
        print(f"Input tokens: {input_tokens}")
        print(f"Output tokens: {output_tokens}")
        print(f"Total tokens: {total_tokens}")
        print(f"Estimated cost: ${total_cost:.6f}")
        print(f"Model: {model_id}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    success = test_nova_pro_direct()
    if success:
        print("\n🎉 Amazon Nova Pro integration test passed!")
    else:
        print("\n❌ Amazon Nova Pro integration test failed!")