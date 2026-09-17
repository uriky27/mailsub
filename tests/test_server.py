"""Tests for mailsub orchestration helpers."""
from server import save_original_file


def test_save_original_file_preserves_content(tmp_path, monkeypatch):
    """Downloaded originals are retained unchanged in the configured archive."""
    monkeypatch.setenv("MAILSUB_ARCHIVE_DIR", str(tmp_path))
    original_data = b"original file content"

    archive_path = save_original_file(original_data, "document.txt")

    assert archive_path.parent == tmp_path
    assert archive_path.name.endswith("-document.txt")
    assert archive_path.read_bytes() == original_data