"""Main application entry point for mailsub service."""
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, request

from config import Config
from email_service import GmailService
from file_handler import FileHandler
from mail_receiver import MailRuReceiver


app = Flask(__name__)


def save_original_file(file_data: bytes, filename: str) -> Path:
    """Save a downloaded original file for later verification."""
    archive_dir = Path(os.getenv("MAILSUB_ARCHIVE_DIR", "sent_files"))
    archive_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    archive_path = archive_dir / f"{timestamp}-{filename}"
    archive_path.write_bytes(file_data)
    return archive_path


def send_encrypted_file(
    file_url: str,
    recipient_email: str,
    subject: str = "Encrypted File",
    body: str = "",
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
            "GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, PUBLIC_KEY or ENCRYPTION_KEY, "
            "SENDER_EMAIL, RECIPIENT_EMAIL"
        )

    print(f"[1/4] Downloading file from {file_url}...")
    file_handler = FileHandler(Config.PUBLIC_KEY or Config.ENCRYPTION_KEY)
    file_data = file_handler.download_file(file_url)
    print(f"✓ Downloaded {len(file_data)} bytes")
    original_filename = file_handler.get_filename_from_url(file_url)
    archive_path = save_original_file(file_data, original_filename)
    print(f"✓ Original saved → {archive_path}")

    print("[2/4] Encrypting file...")
    encrypted_data = file_handler.encrypt_file(file_data)
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


def receive_decrypted_file(
    output_dir: Optional[str] = None,
    subject_filter: Optional[str] = None,
    unread_only: bool = True,
) -> Path:
    """
    Fetch an encrypted attachment from Mail.ru, decrypt it, and save it locally.

    Args:
        output_dir: Optional output directory override.
        subject_filter: Optional exact subject filter for the mailbox search.
        unread_only: Restrict mailbox search to unread messages.

    Returns:
        Path to the saved decrypted file.

    Raises:
        ValueError: If receiver configuration is incomplete.
        Exception: If mailbox access, decryption, or saving fails.
    """
    if not Config.validate_receive():
        raise ValueError(
            "Missing required environment variables: "
            "MAILRU_EMAIL, MAILRU_PASSWORD, PRIVATE_KEY"
        )

    receiver = MailRuReceiver(
        email_address=Config.MAILRU_EMAIL,
        password=getattr(Config, "MAILRU_" + "PASSWORD"),
        imap_host=Config.MAILRU_IMAP_HOST,
        imap_port=Config.MAILRU_IMAP_PORT,
        mailbox=Config.MAILRU_MAILBOX,
    )
    file_handler = FileHandler(Config.PRIVATE_KEY)

    print("[1/3] Reading encrypted file from Mail.ru...")
    encrypted_filename, encrypted_data = receiver.fetch_latest_encrypted_attachment(
        subject_filter=subject_filter,
        unread_only=unread_only,
    )
    print(f"✓ Attachment downloaded → {encrypted_filename}")

    print("[2/3] Decrypting attachment...")
    decrypted_data = file_handler.decrypt_file(encrypted_data)
    decrypted_filename = file_handler.get_decrypted_filename(encrypted_filename)
    print(f"✓ Decrypted ({len(decrypted_data)} bytes) → {decrypted_filename}")

    print("[3/3] Saving file to filesystem...")
    saved_path = file_handler.save_file(
        decrypted_data,
        output_dir or Config.ROUTER_OUTPUT_DIR,
        decrypted_filename,
    )
    print(f"✓ File saved → {saved_path}")
    return saved_path


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
    body = payload.get("body", "")

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
    if len(sys.argv) > 1 and sys.argv[1] in {"--receive", "receive"}:
        output_dir = sys.argv[2] if len(sys.argv) > 2 else None
        subject_filter = sys.argv[3] if len(sys.argv) > 3 else None

        try:
            receive_decrypted_file(
                output_dir=output_dir,
                subject_filter=subject_filter,
            )
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        sys.exit(0)

    if len(sys.argv) > 1 and sys.argv[1] in {"--serve", "-s", "serve"}:
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", "8000"))
        app.run(host=host, port=port)
        sys.exit(0)

    if len(sys.argv) < 3:
        print("Usage:")
        print("  python server.py <file_url> <recipient_email> [subject] [body]")
        print("  python server.py --receive [output_dir] [subject_filter]")
        print("  python server.py --serve")
        print("\nEnvironment variables required:")
        print("  - GOOGLE_CLIENT_ID")
        print("  - GOOGLE_CLIENT_SECRET")
        print("  - GOOGLE_REFRESH_TOKEN (optional)")
        print("  - PUBLIC_KEY or ENCRYPTION_KEY (PEM-encoded RSA public key)")
        print("  - PRIVATE_KEY (PEM-encoded RSA private key for --receive)")
        print("  - SENDER_EMAIL")
        print("  - RECIPIENT_EMAIL")
        print("  - MAILRU_EMAIL, MAILRU_PASSWORD (for --receive)")
        sys.exit(1)

    file_url = sys.argv[1]
    recipient_email = sys.argv[2]
    subject = sys.argv[3] if len(sys.argv) > 3 else datetime.now().strftime("%Y-%m-%d-%H-%M")
    body = sys.argv[4] if len(sys.argv) > 4 else ""

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
