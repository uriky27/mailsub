"""Tests for mailsub core functionality."""
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from file_handler import FileHandler


@pytest.fixture
def encryption_key():
    """Generate a test RSA private key in PEM format."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()


@pytest.fixture
def file_handler(encryption_key):
    """Create a FileHandler instance for testing."""
    return FileHandler(encryption_key)


class TestFileHandler:
    """Test FileHandler encryption/decryption."""
    
    def test_encrypt_decrypt_roundtrip(self, file_handler):
        """Test that encrypting and decrypting returns original data."""
        original_data = b"This is a test file content"
        
        encrypted = file_handler.encrypt_file(original_data)
        assert encrypted != original_data
        
        decrypted = file_handler.decrypt_file(encrypted)
        assert decrypted == original_data
    
    def test_get_filename_from_url(self, file_handler):
        """Test filename extraction from URL."""
        test_cases = [
            ("https://example.com/documents/file.pdf", "file.pdf"),
            ("https://example.com/path/to/image.png", "image.png"),
            ("https://example.com/", "downloaded_file"),
        ]
        
        for url, expected in test_cases:
            assert file_handler.get_filename_from_url(url) == expected
    
    def test_get_encrypted_filename(self, file_handler):
        """Test encrypted filename generation."""
        result = file_handler.get_encrypted_filename("document.pdf")
        assert result == "document.pdf.encrypted"


class TestDownloadFile:
    """Test file downloading (requires network)."""
    
    @pytest.mark.integration
    def test_download_small_file(self, file_handler):
        """Test downloading a small file from httpbin."""
        url = "https://httpbin.org/robots.txt"
        data = file_handler.download_file(url)
        
        assert isinstance(data, bytes)
        assert len(data) > 0
    
    def test_download_timeout(self, file_handler):
        """Test download timeout handling."""
        # Use a slow endpoint
        with pytest.raises(Exception):
            file_handler.download_file(
                "https://httpbin.org/delay/10",
                timeout=1
            )
