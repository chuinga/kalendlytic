"""
Encryption utilities for OAuth tokens and sensitive data using AWS KMS.
"""

import base64
import os
from typing import str
from .aws_clients import get_kms_client


def get_kms_key_id() -> str:
    """Get KMS key ID from environment variables."""
    key_id = os.environ.get('KMS_KEY_ID')
    if not key_id:
        raise ValueError("KMS_KEY_ID environment variable not set")
    return key_id


def encrypt_token(plaintext_token: str) -> str:
    """
    Encrypt a token using AWS KMS.
    
    Args:
        plaintext_token: The token to encrypt
        
    Returns:
        Base64-encoded encrypted token
    """
    try:
        kms_client = get_kms_client()
        key_id = get_kms_key_id()
        
        response = kms_client.encrypt(
            KeyId=key_id,
            Plaintext=plaintext_token.encode('utf-8')
        )
        
        # Return base64-encoded ciphertext
        return base64.b64encode(response['CiphertextBlob']).decode('utf-8')
        
    except Exception as e:
        raise Exception(f"Failed to encrypt token: {str(e)}")


def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypt a token using AWS KMS.
    
    Args:
        encrypted_token: Base64-encoded encrypted token
        
    Returns:
        Decrypted plaintext token
    """
    try:
        kms_client = get_kms_client()
        
        # Decode base64 ciphertext
        ciphertext_blob = base64.b64decode(encrypted_token.encode('utf-8'))
        
        response = kms_client.decrypt(
            CiphertextBlob=ciphertext_blob
        )
        
        return response['Plaintext'].decode('utf-8')
        
    except Exception as e:
        raise Exception(f"Failed to decrypt token: {str(e)}")