#!/usr/bin/env python3
"""
Quick test script to verify Amazon Nova Pro integration.
"""

import sys
import os
sys.path.append('src')

from services.bedrock_client import BedrockClient, BedrockClientError
from config.bedrock_config import BedrockConfig

def test_nova_pro_config():
    """Test Nova Pro configuration."""
    print("=== Testing Amazon Nova Pro Configuration ===")
    
    # Test configuration
    config = BedrockConfig.get_config()
    print(f"Model ID: {config['model_id']}")
    print(f"Region: {config['region_name']}")
    print(f"Input token cost: ${config['input_token_cost_per_1k']}/1K tokens")
    print(f"Output token cost: ${config['output_token_cost_per_1k']}/1K tokens")
    
    # Test client initialization
    try:
        client = BedrockClient(region_name=config['region_name'])
        print(f"✓ BedrockClient initialized successfully")
        print(f"✓ Model ID: {client.MODEL_ID}")
        print(f"✓ Region: {client.region_name}")
        
        # Test a simple prompt (this will make an actual API call)
        print("\n=== Testing Nova Pro API Call ===")
        prompt = "Hello! Please respond with a brief greeting and confirm you are Amazon Nova Pro."
        
        response = client.invoke_model(prompt=prompt, max_tokens=100)
        
        print(f"✓ API call successful!")
        print(f"Response: {response.content}")
        print(f"Tokens used: {response.token_usage.total_tokens}")
        print(f"Cost: ${response.token_usage.estimated_cost_usd:.4f}")
        print(f"Model: {response.model_id}")
        
        return True
        
    except BedrockClientError as e:
        print(f"✗ Bedrock client error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_nova_pro_config()
    if success:
        print("\n🎉 Amazon Nova Pro integration test passed!")
    else:
        print("\n❌ Amazon Nova Pro integration test failed!")
        sys.exit(1)