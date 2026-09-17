"""Mail.ru IMAP receiver for encrypted attachments."""
from email import message_from_bytes
from email.policy import default
import imaplib
from typing import Optional, Tuple


class MailRuReceiver:
    """Fetch encrypted attachments from a Mail.ru mailbox."""

    def __init__(
        self,
        email_address: str,
        password: str,
        imap_host: str = "imap.mail.ru",
        imap_port: int = 993,
        mailbox: str = "INBOX",
    ):
        """
        Initialize IMAP receiver settings.

        Args:
            email_address: Mailbox login.
            password: Mailbox password or app password.
            imap_host: IMAP server hostname.
            imap_port: IMAP server port.
            mailbox: Mailbox folder to read from.
        """
        self.email_address = email_address
        self.password = password
        self.imap_host = imap_host
        self.imap_port = imap_port
        self.mailbox = mailbox

    @staticmethod
    def extract_encrypted_attachment(
        raw_message: bytes,
        filename_suffix: str = ".encrypted",
    ) -> Tuple[str, bytes]:
        """
        Extract the first encrypted attachment from a raw email message.

        Args:
            raw_message: RFC822 email bytes.
            filename_suffix: Attachment filename suffix to match.

        Returns:
            Attachment filename and content.

        Raises:
            ValueError: If the message has no matching attachment.
        """
        message = message_from_bytes(raw_message, policy=default)

        for part in message.iter_attachments():
            filename = part.get_filename()
            if filename and filename.endswith(filename_suffix):
                payload = part.get_payload(decode=True)
                if payload is None:
                    raise ValueError(f"Attachment {filename} is empty.")
                return filename, payload

        raise ValueError("No encrypted attachment found in message.")

    def fetch_latest_encrypted_attachment(
        self,
        subject_filter: Optional[str] = None,
        unread_only: bool = True,
    ) -> Tuple[str, bytes]:
        """
        Fetch the newest encrypted attachment from the mailbox.

        Args:
            subject_filter: Optional exact subject match filter.
            unread_only: Restrict search to unread messages.

        Returns:
            Attachment filename and content.

        Raises:
            ValueError: If no matching email with encrypted attachment is found.
            imaplib.IMAP4.error: If IMAP authentication or commands fail.
        """
        search_parts = ["UNSEEN" if unread_only else "ALL"]
        if subject_filter:
            search_parts.extend(["SUBJECT", f'"{subject_filter}"'])

        with imaplib.IMAP4_SSL(self.imap_host, self.imap_port) as mailbox:
            mailbox.login(self.email_address, self.password)
            mailbox.select(self.mailbox)
            status, data = mailbox.search(None, *search_parts)
            if status != "OK":
                raise ValueError("Unable to search Mail.ru mailbox.")

            message_ids = data[0].split()
            for message_id in reversed(message_ids):
                fetch_status, message_data = mailbox.fetch(message_id, "(RFC822)")
                if fetch_status != "OK":
                    continue

                for part in message_data:
                    if not isinstance(part, tuple):
                        continue
                    try:
                        return self.extract_encrypted_attachment(part[1])
                    except ValueError:
                        break

        raise ValueError("No encrypted attachment found in Mail.ru mailbox.")
