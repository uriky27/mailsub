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
    
    # Encryption key (must be 32 bytes for AES-256)
    ENCRYPTION_KEY: Optional[str] = os.environ.get("ENCRYPTION_KEY")
    
    # Email settings
    SENDER_EMAIL: Optional[str] = os.environ.get("SENDER_EMAIL")
    RECIPIENT_EMAIL: Optional[str] = os.environ.get("RECIPIENT_EMAIL")
    
    @staticmethod
    def validate() -> bool:
        """Validate required configuration is set."""
        required = [
            Config.GOOGLE_CLIENT_ID,
            Config.GOOGLE_CLIENT_SECRET,
            Config.ENCRYPTION_KEY,
            Config.SENDER_EMAIL,
            Config.RECIPIENT_EMAIL,
        ]
        return all(required)
