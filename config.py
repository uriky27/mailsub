"""Configuration and environment management for mailsub."""
import os
from typing import Optional

from dotenv import load_dotenv


load_dotenv()


class Config:
    """Configuration class for sensitive data and settings."""
    
    # Google API Configuration
    GOOGLE_CLIENT_ID: Optional[str] = os.environ.get("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: Optional[str] = os.environ.get("GOOGLE_CLIENT_SECRET")
    GOOGLE_REFRESH_TOKEN: Optional[str] = os.environ.get("GOOGLE_REFRESH_TOKEN")
    
    # Public encryption key used by the server to encrypt outbound files.
    PUBLIC_KEY: Optional[str] = os.environ.get("PUBLIC_KEY")
    # Backward compatibility for older deployments using ENCRYPTION_KEY.
    ENCRYPTION_KEY: Optional[str] = os.environ.get("ENCRYPTION_KEY") or PUBLIC_KEY
    PRIVATE_KEY: Optional[str] = os.environ.get("PRIVATE_KEY")
    
    # Email settings
    SENDER_EMAIL: Optional[str] = os.environ.get("SENDER_EMAIL")
    RECIPIENT_EMAIL: Optional[str] = os.environ.get("RECIPIENT_EMAIL")
    MAILRU_EMAIL: Optional[str] = os.environ.get("MAILRU_EMAIL")
    MAILRU_PASSWORD: Optional[str] = os.environ.get("MAILRU_PASSWORD")
    MAILRU_IMAP_HOST: str = os.environ.get("MAILRU_IMAP_HOST", "imap.mail.ru")
    MAILRU_IMAP_PORT: int = int(os.environ.get("MAILRU_IMAP_PORT", "993"))
    MAILRU_MAILBOX: str = os.environ.get("MAILRU_MAILBOX", "INBOX")
    ROUTER_OUTPUT_DIR: str = os.environ.get("ROUTER_OUTPUT_DIR", "router_files")
    
    @staticmethod
    def validate() -> bool:
        """Validate required configuration is set."""
        encryption_key = Config.PUBLIC_KEY or Config.ENCRYPTION_KEY
        required = [
            Config.GOOGLE_CLIENT_ID,
            Config.GOOGLE_CLIENT_SECRET,
            encryption_key,
            Config.SENDER_EMAIL,
            Config.RECIPIENT_EMAIL,
        ]
        return all(required)

    @staticmethod
    def validate_receive() -> bool:
        """Validate required configuration for router-side decryption."""
        required = [
            Config.MAILRU_EMAIL,
            Config.MAILRU_PASSWORD,
            Config.PRIVATE_KEY,
        ]
        return all(required)
