import io
import json
import os
import re
import subprocess  # noqa: S404 - fixed argv, no shell
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

from app.core.config import get_settings
from app.core.errors import AppError

ALLOWED = {".pdf": "pdf", ".docx": "docx"}
MIME = {"pdf": "application/pdf", "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
API_ROOT = Path(__file__).resolve().parents[2]
_ENV_KEEP = {"PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP", "TMPDIR", "HOME", "LANG", "LC_ALL"}
MAX_ZIP_ENTRIES, MAX_ZIP_TOTAL, MAX_RATIO = 1000, 40 * 1024 * 1024, 100


@dataclass
class Parsed:
    kind: str
    text: str
    pages: int
    truncated: bool


def safe_filename(name: str) -> str:
    """Display name only. It is never used as a path."""
    base = re.split(r"[\\/]", name or "")[-1]
    base = re.sub(r"[^\w.\- ()]", "_", base, flags=re.UNICODE).strip(" .")
    return (base or "resume")[:120]


def detect_kind(filename: str, data: bytes) -> str:
    ext = Path(filename or "").suffix.lower()
    kind = ALLOWED.get(ext)
    if kind is None:
        raise AppError(415, "unsupported_type", "Only PDF and DOCX files are accepted.")
    if not data:
        raise AppError(422, "empty_file", "The file is empty.")
    magic_ok = data.startswith(b"%PDF-") if kind == "pdf" else data.startswith(b"PK\x03\x04")
    if not magic_ok:
        raise AppError(415, "content_mismatch", f"This file's contents don't look like a real {kind.upper()}.")
    if kind == "docx":
        _check_docx_container(data)
    return kind


def _check_docx_container(data: bytes) -> None:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            infos = zf.infolist()
            names = [i.filename for i in infos]
            if len(infos) > MAX_ZIP_ENTRIES:
                raise AppError(422, "file_too_complex", "The document has too many parts.")
            if "word/document.xml" not in names:
                raise AppError(415, "content_mismatch", "This isn't a Word document.")
            if any("vbaproject" in n.lower() or n.lower().endswith((".exe", ".dll", ".js", ".vbs")) for n in names):
                raise AppError(422, "macros_not_allowed", "Documents containing macros or executables are not accepted.")
            if sum(i.file_size for i in infos) > MAX_ZIP_TOTAL:
                raise AppError(422, "file_too_complex", "The document expands to an unsafe size.")
            for i in infos:
                if i.flag_bits & 0x1:
                    raise AppError(422, "encrypted_docx", "Encrypted documents are not supported.")
                if i.file_size > 1_000_000 and i.file_size / max(i.compress_size, 1) > MAX_RATIO:
                    raise AppError(422, "file_too_complex", "The document looks like a compression bomb.")
    except zipfile.BadZipFile:
        raise AppError(415, "content_mismatch", "This isn't a valid DOCX file.") from None


def extract_text(kind: str, data: bytes) -> Parsed:
    """Parse in a child process with a timeout and without the app's secrets in its environment."""
    s = get_settings()
    env = {k: v for k, v in os.environ.items() if k in _ENV_KEEP}
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"upload.{kind}"
        path.write_bytes(data)
        try:
            proc = subprocess.run(  # noqa: S603
                [sys.executable, "-m", "app.resumes.parse_worker", kind, str(path)],
                capture_output=True,
                text=True,
                timeout=s.parse_timeout_seconds,
                cwd=API_ROOT,
                env=env,
                check=False,
            )
        except subprocess.TimeoutExpired:
            raise AppError(422, "parse_timeout", "Reading this file took too long, so it was stopped. Try a simpler export.") from None
    try:
        res = json.loads(proc.stdout)
    except ValueError:
        raise AppError(422, "parse_failed", "The file could not be read.") from None
    if not res.get("ok"):
        raise AppError(422, res.get("code", "parse_failed"), res.get("message", "The file could not be read."))
    if len(res["text"].strip()) < 40:
        raise AppError(422, "no_text", "No readable text was found. Scanned or image-only resumes are not supported yet; export a text-based PDF or DOCX.")
    return Parsed(kind=kind, text=res["text"], pages=res["pages"], truncated=res.get("truncated", False))
