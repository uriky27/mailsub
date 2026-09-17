"""Tests for mailsub orchestration helpers."""
from server import receive_decrypted_file, save_original_file


def test_save_original_file_preserves_content(tmp_path, monkeypatch):
    """Downloaded originals are retained unchanged in the configured archive."""
    monkeypatch.setenv("MAILSUB_ARCHIVE_DIR", str(tmp_path))
    original_data = b"original file content"

    archive_path = save_original_file(original_data, "document.txt")

    assert archive_path.parent == tmp_path
    assert archive_path.name.endswith("-document.txt")
    assert archive_path.read_bytes() == original_data


def test_receive_decrypted_file_saves_attachment(tmp_path, monkeypatch):
    """Router flow decrypts the Mail.ru attachment and writes the file to disk."""
    original_data = b"router payload"

    class FakeReceiver:
        def __init__(self, *args, **kwargs):
            pass

        def fetch_latest_encrypted_attachment(self, subject_filter=None, unread_only=True):
            return "config.txt.encrypted", encrypted_data

    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    from file_handler import FileHandler

    encrypted_data = FileHandler(public_pem).encrypt_file(original_data)

    monkeypatch.setattr("server.MailRuReceiver", FakeReceiver)
    monkeypatch.setattr("server.Config.validate_receive", staticmethod(lambda: True))
    monkeypatch.setattr("server.Config.PRIVATE_KEY", private_pem)
    monkeypatch.setattr("server.Config.MAILRU_EMAIL", "router@mail.ru")
    monkeypatch.setattr("server.Config.MAILRU_PASSWORD", "password")
    monkeypatch.setattr("server.Config.MAILRU_IMAP_HOST", "imap.mail.ru")
    monkeypatch.setattr("server.Config.MAILRU_IMAP_PORT", 993)
    monkeypatch.setattr("server.Config.MAILRU_MAILBOX", "INBOX")

    saved_path = receive_decrypted_file(output_dir=str(tmp_path))

    assert saved_path == tmp_path / "config.txt"
    assert saved_path.read_bytes() == original_data