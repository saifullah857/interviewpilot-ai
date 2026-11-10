"""Runs in a SEPARATE process (python -m app.resumes.parse_worker <pdf|docx> <path>) with a timeout and a scrubbed
environment, so a hostile or broken file can only hang or crash this process, never the API.
It must stay self-contained: it imports nothing from the rest of the app (no settings, no secrets)."""

import json
import re
import sys
import zipfile

MAX_PAGES = 15
MAX_CHARS = 60_000
MAX_XML_BYTES = 20 * 1024 * 1024
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _clean(text: str) -> str:
    text = _CONTROL.sub("", text.replace("\r\n", "\n").replace("\r", "\n"))
    text = re.sub(r"[ \t\u00a0]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _fail(code: str, message: str) -> dict:
    return {"ok": False, "code": code, "message": message}


def _pdf(path: str) -> dict:
    from pypdf import PdfReader

    reader = PdfReader(path)
    if reader.is_encrypted:
        return _fail("encrypted_pdf", "Password-protected PDFs are not supported. Export an unprotected copy and try again.")
    if len(reader.pages) > MAX_PAGES:
        return _fail("too_many_pages", f"The PDF has more than {MAX_PAGES} pages. A resume should be shorter.")
    parts = [(p.extract_text() or "") for p in reader.pages]
    return {"ok": True, "text": parts, "pages": len(parts)}


def _docx(path: str) -> dict:
    from defusedxml import ElementTree as ET

    ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    with zipfile.ZipFile(path) as zf:
        with zf.open("word/document.xml") as fh:
            raw = fh.read(MAX_XML_BYTES + 1)
    if len(raw) > MAX_XML_BYTES:
        return _fail("file_too_complex", "The document is too large to read safely.")
    root = ET.fromstring(raw)  # defusedxml refuses DTDs and entity tricks
    lines = []
    for para in root.iter(f"{ns}p"):
        buf = []
        for el in para.iter():
            if el.tag == f"{ns}t" and el.text:
                buf.append(el.text)
            elif el.tag == f"{ns}tab":
                buf.append("\t")
            elif el.tag in (f"{ns}br", f"{ns}cr"):
                buf.append("\n")
        lines.append("".join(buf))
    return {"ok": True, "text": ["\n".join(lines)], "pages": 1}


def main(argv: list[str]) -> int:
    kind, path = argv[1], argv[2]
    try:
        try:
            import resource  # POSIX only; on Windows the timeout in the parent is the guard

            resource.setrlimit(resource.RLIMIT_AS, (1_500_000_000, 1_500_000_000))
        except (ImportError, ValueError, OSError):
            pass
        res = _pdf(path) if kind == "pdf" else _docx(path)
        if res["ok"]:
            text = _clean("\n\n".join(res.pop("text")))
            res["truncated"] = len(text) > MAX_CHARS
            res["text"] = text[:MAX_CHARS]
    except MemoryError:
        res = _fail("file_too_complex", "The file is too complex to read safely.")
    except Exception as e:  # noqa: BLE001 - any parser failure becomes a clean error, never a crash
        res = _fail("corrupt_file", f"The file could not be read ({type(e).__name__}). Is it a valid {kind.upper()}?")
    sys.stdout.write(json.dumps(res))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
