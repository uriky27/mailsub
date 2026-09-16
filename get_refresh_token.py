#!/usr/bin/env python3
"""
Helper script to obtain Google OAuth 2.0 refresh token.
Run this once locally to generate the refresh token for use on remote servers.
"""
import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def get_refresh_token():
    """Obtain refresh token from Google OAuth 2.0 flow."""
    if not os.path.exists("credentials.json"):
        print("ERROR: credentials.json not found in current directory.")
        print("Download it from Google Cloud Console:")
        print("  https://console.cloud.google.com/")
        print("  Credentials → Create Credentials → OAuth 2.0 Client ID → Desktop")
        return None
    
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json",
            SCOPES,
        )
        creds = flow.run_local_server(port=0)
        
        if creds.refresh_token:
            print("\n✓ Successfully obtained refresh token!")
            print("\nAdd this to your .env file:")
            print(f"GOOGLE_REFRESH_TOKEN={creds.refresh_token}")
            return creds.refresh_token
        else:
            print("ERROR: No refresh token received from Google.")
            return None
    except Exception as e:
        print(f"ERROR during OAuth: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure credentials.json exists and is valid")
        print("2. Check that Gmail API is enabled in Google Cloud Console")
        print("3. Try deleting the credentials file and downloading a new one")
        return None

if __name__ == "__main__":
    print("Google OAuth 2.0 Refresh Token Generator")
    print("=" * 50)
    print("\nThis will open your browser for Google OAuth approval.")
    print("Make sure you're logged into the Gmail account you want to use.\n")
    
    token = get_refresh_token()
    if token:
        print("\nDone! Save this token securely.")
    else:
        print("\nFailed to obtain token. See errors above.")
