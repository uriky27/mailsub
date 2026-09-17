# mailsub - Encrypted File Transfer Service

Download a file from a URL, encrypt it, and send it via email using Google Gmail API. The repository also includes a router-side flow that reads the encrypted attachment from Mail.ru, decrypts it, and saves it to the local filesystem.

## Features
- 🔒 **RSA Encryption/Decryption** - Encrypt on the sender, decrypt on the router with the private key
- 📧 **Gmail Integration** - Send encrypted files via Google Gmail API
- 📥 **Mail.ru IMAP Retrieval** - Read encrypted attachments from a Mail.ru inbox
- 🌐 **URL Download** - Download files from any web URL
- 🔑 **OAuth 2.0 Authentication** - Secure Google API access

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Google OAuth 2.0
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Gmail API
4. Create OAuth 2.0 credentials (Desktop application)
5. Download credentials as `credentials.json` and place in project root
6. Run the app once to generate refresh token:
   ```bash
   python server.py https://example.com/sample.txt recipient@gmail.com
   ```
   This will open a browser for authentication and save the refresh token.

### 3. Generate RSA Key Pair
```bash
python - <<'PY'
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
print(private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.TraditionalOpenSSL,
    encryption_algorithm=serialization.NoEncryption(),
).decode())
print(private_key.public_key().public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
).decode())
PY
```

### 4. Configure Environment
Copy `.env.example` to `.env` and fill in your values:
```bash
cp .env.example .env
```

### 5. Run the Application

**Command Line Usage:**
```bash
python server.py <file_url> <recipient_email> [subject] [body]

# Example:
python server.py https://example.com/document.pdf user@gmail.com "Important Document" "Here is your encrypted file"
```

**Python API Usage:**
```python
from server import send_encrypted_file

send_encrypted_file(
    file_url="https://example.com/file.zip",
    recipient_email="user@gmail.com",
    subject="Encrypted File Transfer",
    body="Your encrypted file is ready."
)
```

**Router-side receive/decrypt usage:**
```bash
python server.py --receive /data/mailsub "Encrypted File"
```

## Architecture

- **config.py** - Configuration and environment management
- **file_handler.py** - Download and encryption utilities
- **email_service.py** - Gmail API integration
- **server.py** - Main orchestration logic

## Security Considerations

⚠️ **Important:**
- Keep `ENCRYPTION_KEY` and Google credentials secure (never commit to git)
- Use `.env` file and add to `.gitignore`
- Refresh tokens should be stored securely
- Use strong, unpredictable keys for encryption

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GOOGLE_CLIENT_ID` | OAuth 2.0 Client ID from Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | OAuth 2.0 Client Secret (keep secret!) |
| `GOOGLE_REFRESH_TOKEN` | Refresh token (auto-generated after first auth) |
| `PUBLIC_KEY` | PEM-encoded RSA public key used to encrypt outgoing files |
| `ENCRYPTION_KEY` | Backward-compatible alias for `PUBLIC_KEY` |
| `PRIVATE_KEY` | PEM-encoded RSA private key used by the router to decrypt files |
| `SENDER_EMAIL` | Gmail address to send from |
| `RECIPIENT_EMAIL` | Default recipient email |
| `MAILRU_EMAIL` | Mail.ru mailbox address used by the router |
| `MAILRU_PASSWORD` | Mail.ru mailbox password or app password |
| `MAILRU_IMAP_HOST` | IMAP host for Mail.ru (`imap.mail.ru` by default) |
| `MAILRU_IMAP_PORT` | IMAP port for Mail.ru (`993` by default) |
| `MAILRU_MAILBOX` | IMAP mailbox/folder to scan (`INBOX` by default) |
| `ROUTER_OUTPUT_DIR` | Directory where decrypted files are stored on the router |

## Testing

```bash
# Download a small test file and encrypt it
python server.py https://httpbin.org/image/png test@example.com "Test Image" "Encrypted image file"

# Read the latest encrypted attachment from Mail.ru and save the decrypted file
python server.py --receive /tmp/mailsub-router
```

## Remote Deployment Workflow

This project is designed for local development in VS Code and deployment to a Linux server via SSH.

### 1. Prepare the server
```bash
sudo ./scripts/setup-server.sh
```

Set these environment variables before running the script:
```bash
export GIT_REPO_URL="https://github.com/your-user/mailsub.git"
export REPO_PATH="/opt/mailsub"
export BRANCH="main"
```

### 2. Configure secrets on the server
Put these files in `/opt/mailsub`:
- `.env`
- `credentials.json`

Do not store them in Git.

### 3. Install systemd service
```bash
sudo cp /opt/mailsub/systemd/mailsub.service /etc/systemd/system/mailsub.service
sudo cp /opt/mailsub/systemd/mailsub.timer /etc/systemd/system/mailsub.timer
sudo systemctl daemon-reload
sudo systemctl enable --now mailsub.timer
```

### 4. Deploy from VS Code
Use the built-in task:
- Terminal → Run Task → `Deploy to remote server`

Or run directly:
```bash
REMOTE_USER=deploy REMOTE_HOST=123.45.67.89 REMOTE_PATH=/opt/mailsub REMOTE_BRANCH=main ./scripts/deploy.sh
```

### 5. Check service status
```bash
sudo systemctl status mailsub
sudo journalctl -u mailsub -f
```

This gives you a standard workflow:
- edit in VS Code
- push to GitHub
- deploy from VS Code over SSH
- restart the systemd service on the remote server
