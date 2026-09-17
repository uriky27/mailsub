"""Tests for Mail.ru encrypted attachment retrieval."""
from email.message import EmailMessage

import pytest

from mail_receiver import MailRuReceiver


def test_extract_encrypted_attachment_returns_matching_file():
    """Matching encrypted attachment is returned from the email payload."""
    message = EmailMessage()
    message["Subject"] = "Encrypted file"
    message.set_content("body")
    message.add_attachment(
        b"encrypted-bytes",
        maintype="application",
        subtype="octet-stream",
        filename="backup.tar.encrypted",
    )

    filename, payload = MailRuReceiver.extract_encrypted_attachment(message.as_bytes())

    assert filename == "backup.tar.encrypted"
    assert payload == b"encrypted-bytes"


def test_extract_encrypted_attachment_raises_without_matching_file():
    """Messages without encrypted attachments are rejected."""
    message = EmailMessage()
    message["Subject"] = "Plain file"
    message.set_content("body")
    message.add_attachment(
        b"plain-bytes",
        maintype="application",
        subtype="octet-stream",
        filename="backup.tar",
    )

    with pytest.raises(ValueError):
        MailRuReceiver.extract_encrypted_attachment(message.as_bytes())
