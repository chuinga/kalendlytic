"""
Demo script showing how to use the Bedrock Claude Sonnet 4.5 client
for meeting scheduling scenarios.
"""

import os
import sys
import json
from datetime import datetime, timedelta

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from services.bedrock_client import BedrockClient, BedrockClientError
from services.scheduling_agent import SchedulingAgent, SchedulingAgentError
from config.bedrock_config import BedrockConfig


def demo_basic_bedrock_client():
    """Demonstrate basic Bedrock client usage."""
    print("=== Basic Bedrock Client Demo ===")
    
    try:
        # Initialize client
        client = BedrockClient()
        
        # Simple prompt
        prompt = "Explain the benefits of AI-powered meeting scheduling in 2 sentences."
        
        print(f"Sending prompt: {prompt}")
        response = client.invoke_model(prompt, max_tokens=200)
        
        print(f"Response: {response.content}")
        print(f"Token usage: {response.token_usage.total_tokens} tokens")
        print(f"Estimated cost: ${response.token_usage.estimated_cost_usd:.4f}")
        
    except BedrockClientError as e:
        print(f"Bedrock client error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def demo_scheduling_agent():
    """Demonstrate scheduling agent functionality."""
    print("\n=== Scheduling Agent Demo ===")
    
    try:
        # Initialize scheduling agent
        agent = SchedulingAgent()
        
        # Sample meeting request
        meeting_request = {
            "title": "Product Planning Meeting",
            "duration_minutes": 60,
            "requested_time": "2024-02-15T14:00:00Z",
            "priority": "high",
            "attendees": ["alice@company.com", "bob@company.com", "charlie@company.com"],
            "description": "Quarterly product planning and roadmap discussion"
        }
        
        # Sample conflicts
        conflicts = [
            {
                "title": "Engineering Standup",
                "start_time": "2024-02-15T14:00:00Z",
                "end_time": "2024-02-15T14:30:00Z",
                "attendees": ["alice@company.com"],
                "priority": "medium"
            }
        ]
        
        # Sample available slots
        available_slots = [
            {"start_time": "2024-02-15T15:00:00Z", "end_time": "2024-02-15T16:00:00Z"},
            {"start_time": "2024-02-15T16:30:00Z", "end_time": "2024-02-15T17:30:00Z"}
        ]
        
        print("Resolving scheduling conflicts...")
        recommendations = agent.resolve_conflicts(
            meeting_request, conflicts, available_slots
        )
        
        print("AI Recommendations:")
        print(json.dumps(recommendations, indent=2, default=str))
        
    except SchedulingAgentError as e:
        print(f"Scheduling agent error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    print("Bedrock Claude Sonnet 4.5 Demo")
    print("Note: This demo requires valid AWS credentials and Bedrock access")
    print("=" * 60)
    
    # Check configuration
    config = BedrockConfig.get_config()
    print(f"Using region: {config['region_name']}")
    print(f"Model ID: {config['model_id']}")
    
    # Run demos (commented out to avoid actual API calls in testing)
    # demo_basic_bedrock_client()
    # demo_scheduling_agent()
    
    print("\nDemo setup complete. Uncomment function calls to test with real AWS credentials.")