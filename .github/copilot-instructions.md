# Copilot Instructions for mailsub

## Project Overview
**mailsub** is an encrypted file transfer service via email. Core functionality: download a file from a URL → encrypt it with Fernet → send via Gmail API.

## Architecture & Core Concepts

**Module Structure:**
- [config.py](../config.py) - Centralized configuration; secrets via environment variables (`os.environ`)
- [file_handler.py](../file_handler.py) - File download (HTTP) + Fernet encryption/decryption
- [email_service.py](../email_service.py) - Gmail API authentication (OAuth 2.0) + MIME email construction
- [server.py](../server.py) - Orchestrator; CLI entry point + public `send_encrypted_file()` API

**Data Flow:**
1. User provides: `file_url`, `recipient_email`, optional `subject`/`body`
2. `FileHandler.download_file()` → HTTP GET with `requests`
3. `FileHandler.encrypt_file()` → Fernet symmetric encryption
4. `GmailService.authenticate()` → OAuth 2.0 token refresh (requires `credentials.json`)
5. `GmailService.send_encrypted_file()` → MIME multipart with encrypted attachment → Gmail API

## Development Workflows

### Local Setup
```bash
pip install -r requirements.txt
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"  # Generate key
cp .env.example .env  # Configure environment
# First run opens browser for Google OAuth → stores refresh_token
python server.py <url> <recipient@gmail.com>
```

### Running
```bash
# CLI: download, encrypt, email
python server.py https://example.com/file.pdf user@gmail.com "Subject" "Body"

# Python API
from server import send_encrypted_file
send_encrypted_file("https://...", "user@gmail.com")
```

### Testing & Validation
- Manual: test with httpbin.org images/files
- Add `tests/` with pytest when needed (test URL fetch failures, encryption round-trip, Gmail auth mocking)
- Use `.env` for test credentials (never commit actual tokens)

## Project Conventions

### Secrets Management
- **Environment variables only** (`config.py` reads via `os.environ.get()`)
- `.env` file + `.env.example` template (`.env` in `.gitignore`)
- Do NOT pass secrets as CLI arguments or print to logs

### Code Style
- Type hints on all functions (PEP 484), Python 3.8+
- Docstrings: one-line summary + Args/Returns/Raises blocks
- Logging: use `print()` for user feedback; add `logging` module for production debug output

### Module Boundaries
- **file_handler.py**: pure HTTP + crypto, no email logic
- **email_service.py**: pure Gmail API, no file I/O or crypto
- **server.py**: glue layer only; coordinate modules, handle CLI args, error reporting
- Keep modules testable (no side effects like file writes without mocks)

### Error Handling
- Raise `ValueError` for config/input validation (missing env vars, bad URL)
- Raise `requests.RequestException`, `Exception` from Gmail API naturally (caller handles)
- CLI: catch exceptions, print to stderr, exit with code 1

## Integration Points

**Google OAuth 2.0 Flow:**
1. First run: `InstalledAppFlow` opens browser → user approves
2. Stores `refresh_token` in `.env`
3. Subsequent runs: fetch new `access_token` from refresh_token (no browser)
4. Required files: `credentials.json` (downloaded from Cloud Console)

**External Dependencies:**
- `requests==2.31.0` - HTTP downloads
- `cryptography==41.0.7` - Fernet symmetric encryption  
- `google-auth-oauthlib==1.2.0`, `google-api-python-client==2.108.0` - Gmail API

**Constraints:**
- Gmail API daily quota limits (check Cloud Console for usage)
- Fernet key must stay secure; rotating keys requires re-encrypting old attachments
- Downloaded files held in memory (not suitable for >1GB files yet; consider streaming in future)

## Next Steps for Contributors
1. **Caching/Persistence**: Store encrypted files locally before sending (add `save_encrypted_file()` to `FileHandler`)
2. **Streaming for Large Files**: Refactor `download_file()` + encryption to stream chunks (avoid memory overload)
3. **Batch Mode**: Accept CSV of URLs/recipients; queue emails asynchronously
4. **Web API**: Flask/FastAPI endpoint (`POST /send-encrypted`) wrapping `send_encrypted_file()`
5. **Logging & Monitoring**: Replace `print()` with structured logging; track success/failure metrics
