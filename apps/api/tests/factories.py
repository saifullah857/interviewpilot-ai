"""Builders for test files and fake AI replies."""

import io
import json
import zipfile

from pypdf import PdfWriter
from reportlab.pdfgen import canvas

RESUME_LINES = [
    "Ayesha Khan",
    "Email: ayesha.khan@example.com | Phone: +92 300 1234567 | https://github.com/ayesha-k | CNIC 35202-1234567-1",
    "EDUCATION",
    "BS Computer Science, Example University, 2021-2025",
    "EXPERIENCE",
    "Python Intern, Example Tech, Jun 2024 - Aug 2024",
    "Built REST APIs with FastAPI and PostgreSQL; wrote pytest tests.",
    "PROJECTS",
    "Sentiment Analyzer - trained a scikit-learn model on 10,000 reviews, reaching 88% accuracy.",
    "SKILLS",
    "Python, SQL, Git, Pandas, FastAPI",
]


def make_pdf(lines=None) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, invariant=1)  # deterministic bytes so identical text gives an identical file
    y = 800
    for line in lines or RESUME_LINES:
        c.drawString(40, y, line)
        y -= 18
    c.save()
    return buf.getvalue()


def blank_pdf() -> bytes:
    w, buf = PdfWriter(), io.BytesIO()
    w.add_blank_page(300, 300)
    w.write(buf)
    return buf.getvalue()


def encrypted_pdf() -> bytes:
    w, buf = PdfWriter(), io.BytesIO()
    w.add_blank_page(300, 300)
    w.encrypt("secret", algorithm="RC4-128")
    w.write(buf)
    return buf.getvalue()


def make_docx(lines=None, extra: dict[str, bytes] | None = None, with_document=True) -> bytes:
    paras = "".join(f"<w:p><w:r><w:t>{ln.replace('&', '&amp;').replace('<', '&lt;')}</w:t></w:r></w:p>" for ln in (lines or RESUME_LINES))
    doc = f'<?xml version="1.0"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>{paras}</w:body></w:document>'
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        if with_document:
            z.writestr("word/document.xml", doc)
        for name, content in (extra or {}).items():
            z.writestr(name, content)
    return buf.getvalue()


def ai_reply(**override) -> str:
    """A valid, well-grounded extraction of RESUME_LINES."""
    data = {
        "education": [
            {
                "institution": "Example University",
                "degree": "BS",
                "field": "Computer Science",
                "period": "2021-2025",
                "evidence": "BS Computer Science, Example University, 2021-2025",
            }
        ],
        "experience": [
            {
                "title": "Python Intern",
                "organization": "Example Tech",
                "period": "Jun 2024 - Aug 2024",
                "summary": "Built REST APIs and tests.",
                "technologies": ["FastAPI", "PostgreSQL", "pytest"],
                "evidence": "Built REST APIs with FastAPI and PostgreSQL",
            }
        ],
        "projects": [
            {
                "name": "Sentiment Analyzer",
                "description": "Trained a classifier.",
                "technologies": ["scikit-learn"],
                "evidence": "trained a scikit-learn model on 10,000 reviews",
            }
        ],
        "skills": [
            {"name": "Python", "category": "language", "source": "stated", "evidence": "Python, SQL, Git, Pandas, FastAPI"},
            {"name": "SQL", "category": "language", "source": "stated", "evidence": "Python, SQL, Git"},
            {"name": "Machine Learning", "category": "concept", "source": "inferred", "evidence": ""},
        ],
        "achievements": [{"text": "Reached 88% accuracy on a sentiment model", "measurable": True, "evidence": "reaching 88% accuracy"}],
        "inferences": [{"statement": "Likely early-career", "basis": "Internship and a 2025 graduation date", "confidence": "medium"}],
    }
    data.update(override)
    return json.dumps(data)
