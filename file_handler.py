"""File download and encryption utilities."""
import os
from typing import BinaryIO
from urllib.parse import urlparse

import requests
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
    load_pem_public_key,
)


class FileHandler:
    """Handle file download and encryption operations."""
    
    def __init__(self, encryption_key: str):
        """
        Initialize FileHandler with an RSA public key in PEM format.

        The server only needs the public key for encryption. If a private key is
        provided instead, it is kept available for optional decryption in tests or
        local recovery flows.
        """
        self.private_key = None
        self.public_key = None

        try:
            self.private_key = load_pem_private_key(encryption_key.encode(), password=None)
            self.public_key = self.private_key.public_key()
        except ValueError:
            self.public_key = load_pem_public_key(encryption_key.encode())
    
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
        Encrypt file data using the RSA public key.

        RSA can only encrypt messages smaller than the key size minus padding,
        so the payload is split into chunks and encrypted piece by piece.
        """
        block_size = self.public_key.key_size // 8
        hash_size = hashes.SHA256().digest_size
        max_chunk_size = block_size - 2 * hash_size - 2
        encrypted_chunks = []

        for offset in range(0, len(file_data), max_chunk_size):
            chunk = file_data[offset:offset + max_chunk_size]
            encrypted_chunks.append(
                self.public_key.encrypt(
                    chunk,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None,
                    ),
                )
            )

        return b"".join(encrypted_chunks)
    
    def decrypt_file(self, encrypted_data: bytes) -> bytes:
        """
        Decrypt RSA-encrypted file data using the matching private key.
        """
        block_size = self.private_key.key_size // 8
        decrypted_chunks = []

        for offset in range(0, len(encrypted_data), block_size):
            chunk = encrypted_data[offset:offset + block_size]
            if not chunk:
                continue
            decrypted_chunks.append(
                self.private_key.decrypt(
                    chunk,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None,
                    ),
                )
            )

        return b"".join(decrypted_chunks)
    
    def get_filename_from_url(self, url: str) -> str:
        """Extract filename from URL path."""
        path = urlparse(url).path
        return os.path.basename(path) or "downloaded_file"
    
    def get_encrypted_filename(self, original_filename: str) -> str:
        """Generate encrypted filename."""
        return f"{original_filename}.encrypted"
