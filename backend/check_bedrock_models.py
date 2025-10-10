#!/usr/bin/env python3
"""
Check available Bedrock models and inference profiles.
"""

import boto3
import json
from botocore.config import Config

def check_bedrock_availability():
    """Check what's available in Bedrock."""
    print("=== Checking Bedrock Availability ===")
    
    region = "eu-west-1"
    
    try:
        # Create Bedrock clients
        config = Config(region_name=region)
        bedrock_client = boto3.client('bedrock', config=config)
        bedrock_runtime = boto3.client('bedrock-runtime', config=config)
        
        print(f"Region: {region}")
        print()
        
        # List foundation models
        print("=== Available Foundation Models ===")
        try:
            models_response = bedrock_client.list_foundation_models()
            nova_models = [
                model for model in models_response['modelSummaries'] 
                if 'nova' in model['modelId'].lower()
            ]
            
            if nova_models:
                print("Nova models found:")
                for model in nova_models:
                    print(f"  - {model['modelId']} ({model['modelName']})")
                    print(f"    Status: {model.get('modelLifecycle', {}).get('status', 'Unknown')}")
                    print(f"    Input modalities: {model.get('inputModalities', [])}")
                    print(f"    Output modalities: {model.get('outputModalities', [])}")
                    print()
            else:
                print("No Nova models found")
                
        except Exception as e:
            print(f"Error listing foundation models: {e}")
        
        # List inference profiles
        print("=== Available Inference Profiles ===")
        try:
            profiles_response = bedrock_client.list_inference_profiles()
            nova_profiles = [
                profile for profile in profiles_response['inferenceProfileSummaries']
                if 'nova' in profile['inferenceProfileName'].lower() or 
                   'nova' in profile.get('description', '').lower()
            ]
            
            if nova_profiles:
                print("Nova inference profiles found:")
                for profile in nova_profiles:
                    print(f"  - {profile['inferenceProfileName']}")
                    print(f"    ID: {profile['inferenceProfileId']}")
                    print(f"    Status: {profile['status']}")
                    if 'description' in profile:
                        print(f"    Description: {profile['description']}")
                    print()
            else:
                print("No Nova inference profiles found")
                
            # Show all profiles for reference
            print("All available inference profiles:")
            for profile in profiles_response['inferenceProfileSummaries']:
                print(f"  - {profile['inferenceProfileName']} ({profile['inferenceProfileId']})")
                
        except Exception as e:
            print(f"Error listing inference profiles: {e}")
            
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    check_bedrock_availability()