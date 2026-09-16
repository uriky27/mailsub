"""Main application entry point for mailsub service."""
import os
import sys
from typing import Optional

from flask import Flask, jsonify, request

from config import Config
from email_service import GmailService
from file_handler import FileHandler


app = Flask(__name__)


def send_encrypted_file(
    file_url: str,
    recipient_email: str,
    subject: str = "Encrypted File",
    body: str = "Please find the encrypted file attached.",
) -> str:
    """
    Download file from URL, encrypt it, and send via email.
    
    Args:
        file_url: URL to download file from
        recipient_email: Email address to send to
        subject: Email subject line
        body: Email body text
        
    Returns:
        Gmail message ID for the sent email
        
    Raises:
        ValueError: If configuration is incomplete
        Exception: If any step fails
    """
    if not Config.validate():
        raise ValueError(
            "Missing required environment variables: "
            "GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, ENCRYPTION_KEY, "
            "SENDER_EMAIL, RECIPIENT_EMAIL"
        )

    print(f"[1/4] Downloading file from {file_url}...")
    file_handler = FileHandler(Config.ENCRYPTION_KEY)
    file_data = file_handler.download_file(file_url)
    print(f"✓ Downloaded {len(file_data)} bytes")

    print("[2/4] Encrypting file...")
    encrypted_data = file_handler.encrypt_file(file_data)
    original_filename = file_handler.get_filename_from_url(file_url)
    encrypted_filename = file_handler.get_encrypted_filename(original_filename)
    print(f"✓ Encrypted ({len(encrypted_data)} bytes) → {encrypted_filename}")

    print("[3/4] Authenticating with Gmail API...")
    gmail = GmailService(
        client_id=Config.GOOGLE_CLIENT_ID,
        client_secret=Config.GOOGLE_CLIENT_SECRET,
        refresh_token=Config.GOOGLE_REFRESH_TOKEN,
    )
    gmail.authenticate()
    print("✓ Authenticated")

    print(f"[4/4] Sending email to {recipient_email}...")
    message_id = gmail.send_encrypted_file(
        to_email=recipient_email,
        subject=subject,
        body=body,
        encrypted_file_data=encrypted_data,
        filename=encrypted_filename,
        from_email=Config.SENDER_EMAIL,
    )
    print(f"✓ Email sent! Message ID: {message_id}")
    return message_id


@app.get("/health")
def health_check():
    """Return simple health status for remote server monitoring."""
    return jsonify({"status": "ok"})


@app.post("/send-encrypted")
def send_encrypted_http():
    """HTTP endpoint for remote servers to trigger encrypted email delivery."""
    payload = request.get_json(silent=True) or {}
    file_url = payload.get("file_url") or payload.get("url")
    recipient_email = payload.get("recipient_email") or payload.get("to")

    if not file_url or not recipient_email:
        return jsonify({
            "error": "file_url and recipient_email are required"
        }), 400

    subject = payload.get("subject", "Encrypted File")
    body = payload.get("body", "Please find the encrypted file attached.")

    try:
        message_id = send_encrypted_file(
            file_url=file_url,
            recipient_email=recipient_email,
            subject=subject,
            body=body,
        )
        return jsonify({
            "status": "success",
            "message_id": message_id,
        }), 200
    except Exception as exc:
        return jsonify({
            "status": "error",
            "error": str(exc),
        }), 500


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in {"--serve", "-s", "serve"}:
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", "8000"))
        app.run(host=host, port=port)
        sys.exit(0)

    if len(sys.argv) < 3:
        print("Usage:")
        print("  python server.py <file_url> <recipient_email> [subject] [body]")
        print("  python server.py --serve")
        print("\nEnvironment variables required:")
        print("  - GOOGLE_CLIENT_ID")
        print("  - GOOGLE_CLIENT_SECRET")
        print("  - GOOGLE_REFRESH_TOKEN (optional)")
        print("  - ENCRYPTION_KEY (base64-encoded Fernet key)")
        print("  - SENDER_EMAIL")
        print("  - RECIPIENT_EMAIL")
        sys.exit(1)

    file_url = sys.argv[1]
    recipient_email = sys.argv[2]
    subject = sys.argv[3] if len(sys.argv) > 3 else "Encrypted File"
    body = sys.argv[4] if len(sys.argv) > 4 else "Please find the encrypted file attached."

    try:
        send_encrypted_file(
            file_url=file_url,
            recipient_email=recipient_email,
            subject=subject,
            body=body,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
