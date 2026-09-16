"""File download and encryption utilities."""
import io
import os
from typing import BinaryIO
from urllib.parse import urlparse

import requests
from cryptography.fernet import Fernet


class FileHandler:
    """Handle file download and encryption operations."""
    
    def __init__(self, encryption_key: str):
        """
        Initialize FileHandler with encryption key.
        
        Args:
            encryption_key: Base64-encoded Fernet key (32 bytes)
        """
        self.cipher = Fernet(encryption_key.encode())
    
    def download_file(self, url: str, timeout: int = 30) -> bytes:
        """
        Download file from URL.
        
        Args:
            url: URL to download from
            timeout: Request timeout in seconds
            
        Returns:
            File contents as bytes
            
        Raises:
            requests.RequestException: If download fails
        """
        response = requests.get(url, timeout=timeout, stream=False)
        response.raise_for_status()
        return response.content
    
    def encrypt_file(self, file_data: bytes) -> bytes:
        """
        Encrypt file data using Fernet (AES-128 symmetric encryption).
        
        Args:
            file_data: Raw file bytes to encrypt
            
        Returns:
            Encrypted file bytes
        """
        return self.cipher.encrypt(file_data)
    
    def decrypt_file(self, encrypted_data: bytes) -> bytes:
        """
        Decrypt Fernet-encrypted file data.
        
        Args:
            encrypted_data: Encrypted file bytes
            
        Returns:
            Decrypted file bytes
        """
        return self.cipher.decrypt(encrypted_data)
    
    def get_filename_from_url(self, url: str) -> str:
        """Extract filename from URL path."""
        path = urlparse(url).path
        return os.path.basename(path) or "downloaded_file"
    
    def get_encrypted_filename(self, original_filename: str) -> str:
        """Generate encrypted filename."""
        return f"{original_filename}.encrypted"
