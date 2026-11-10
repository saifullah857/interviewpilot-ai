import hashlib
import uuid

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from fastapi.responses import JSONResponse, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.core.config import get_settings
from app.core.db import get_db
from app.core.errors import AppError, not_found
from app.core.ownership import get_owned_or_404
from app.core.rate_limit import analyze_limiter, upload_limiter
from app.llm.base import LLMInvalidOutput, LLMNotConfigured, LLMProvider, LLMRateLimited, LLMUnavailable
from app.llm.factory import get_llm_provider
from app.models.audit import record
from app.models.resume import Resume, ResumeVersion
from app.models.user import User
from app.resumes import analyst, files, roles
from app.resumes.schemas import SCHEMA_VERSION, ParsedResume, ResumeOut, RoleOut, ValidationReport, VersionOut
from app.storage.local import LocalStorage, get_storage

router = APIRouter(tags=["resumes"], dependencies=[Depends(get_current_user)])


def provider_dep() -> LLMProvider:
    try:
        return get_llm_provider()
    except LLMNotConfigured:
        raise AppError(503, "llm_not_configured", "AI analysis isn't set up on this server yet. Your resume is saved and can be analysed once it is.") from None


def _version_out(v: ResumeVersion) -> VersionOut:
    return VersionOut(
        id=v.id,
        created_at=v.created_at,
        provider=v.provider,
        model=v.model,
        schema_version=v.schema_version,
        parsed=ParsedResume.model_validate(v.parsed_json),
        report=ValidationReport.model_validate(v.report_json),
    )


def _out(r: Resume, duplicate: bool = False) -> ResumeOut:
    latest = r.versions[-1] if r.versions else None
    return ResumeOut(
        id=r.id,
        filename=r.filename,
        kind=r.kind,
        size_bytes=r.size_bytes,
        pages=r.pages,
        created_at=r.created_at,
        analyzed=latest is not None,
        duplicate=duplicate,
        latest=_version_out(latest) if latest else None,
        injection_signals=list(r.injection_signals or []),
        truncated=r.truncated,
    )


@router.get("/roles", response_model=list[RoleOut])
def get_roles():
    return roles.list_roles()


@router.get("/resumes", response_model=list[ResumeOut])
def list_resumes(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(Resume).where(Resume.user_id == user.id).order_by(Resume.created_at.desc())).all()
    return [_out(r) for r in rows]


@router.post("/resumes", response_model=ResumeOut, status_code=201)
def upload_resume(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    storage: LocalStorage = Depends(get_storage),
):
    s = get_settings()
    max_bytes = s.max_upload_mb * 1024 * 1024
    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > max_bytes + 64 * 1024:
        raise AppError(413, "file_too_large", f"The file is larger than {s.max_upload_mb} MB.")
    key = str(user.id)
    wait = upload_limiter.retry_after(key, s.uploads_per_hour, 3600)
    if wait:
        raise AppError(429, "rate_limited", "Too many uploads. Try again later.", headers={"Retry-After": str(wait)})
    upload_limiter.add(key)

    data = file.file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise AppError(413, "file_too_large", f"The file is larger than {s.max_upload_mb} MB.")
    kind = files.detect_kind(file.filename or "", data)

    sha = hashlib.sha256(data).hexdigest()
    existing = db.scalars(select(Resume).where(Resume.user_id == user.id, Resume.sha256 == sha)).first()
    if existing:  # same file again: reuse it instead of paying for another analysis
        return JSONResponse(_out(existing, duplicate=True).model_dump(mode="json"), status_code=200)
    if len(db.scalars(select(Resume.id).where(Resume.user_id == user.id)).all()) >= s.max_resumes_per_user:
        raise AppError(409, "resume_limit", f"You can keep up to {s.max_resumes_per_user} resumes. Delete one first.")

    parsed = files.extract_text(kind, data)
    storage_key = storage.put(data)
    resume = Resume(
        user_id=user.id,
        filename=files.safe_filename(file.filename or ""),
        kind=kind,
        size_bytes=len(data),
        pages=parsed.pages,
        sha256=sha,
        storage_key=storage_key,
        text_content=parsed.text,
        truncated=parsed.truncated,
        injection_signals=analyst.injection_signals(parsed.text),
    )
    db.add(resume)
    try:
        db.flush()
        record(db, "resume_uploaded", user.id, resume_id=str(resume.id))
        db.commit()
    except IntegrityError:
        db.rollback()
        storage.delete(storage_key)
        raise AppError(409, "duplicate_resume", "This resume is already uploaded.") from None
    except Exception:
        db.rollback()
        storage.delete(storage_key)
        raise
    return _out(resume)


@router.get("/resumes/{resume_id}", response_model=ResumeOut)
def get_resume(resume_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _out(get_owned_or_404(db, Resume, resume_id, user))


@router.post("/resumes/{resume_id}/analyze", response_model=ResumeOut)
def analyze_resume(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    provider: LLMProvider = Depends(provider_dep),
):
    resume = get_owned_or_404(db, Resume, resume_id, user)
    s = get_settings()
    wait = analyze_limiter.retry_after(str(user.id), s.analyses_per_hour, 3600)
    if wait:
        raise AppError(429, "rate_limited", "Too many analyses. Try again later.", headers={"Retry-After": str(wait)})
    analyze_limiter.add(str(user.id))
    try:
        parsed, report = analyst.analyze(resume.text_content, provider, truncated=resume.truncated)
    except LLMRateLimited as e:
        raise AppError(429, "ai_rate_limited", "The AI provider is busy. Try again shortly.", headers={"Retry-After": str(e.retry_after or 30)}) from None
    except LLMUnavailable:
        raise AppError(503, "llm_unavailable", "The AI service is unavailable right now. Try again later.") from None
    except LLMInvalidOutput:
        raise AppError(502, "analysis_failed", "The AI returned something we couldn't validate. Nothing was saved; try again.") from None
    resume.versions.append(
        ResumeVersion(
            parsed_json=parsed.model_dump(mode="json"),
            report_json=report.model_dump(mode="json"),
            schema_version=SCHEMA_VERSION,
            provider=provider.name,
            model=provider.model,
        )
    )
    record(db, "resume_analyzed", user.id, resume_id=str(resume.id))
    db.commit()
    return _out(resume)


@router.get("/resumes/{resume_id}/fit")
def resume_fit(
    resume_id: uuid.UUID,
    role: str = Query(max_length=80),
    company: str | None = Query(default=None, max_length=80),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    resume = get_owned_or_404(db, Resume, resume_id, user)
    if not resume.versions:
        raise AppError(409, "not_analyzed", "Analyse this resume first.")
    parsed = ParsedResume.model_validate(resume.versions[-1].parsed_json)
    result = roles.fit(parsed, role)
    result["resume_version_id"] = str(resume.versions[-1].id)
    if company:
        from app.companies import service as company_service
        from app.research import service as research_service

        c = company_service.get_selectable_by_slug(db, company)
        result["company"] = research_service.company_fit(parsed, role, c)
    return result


@router.delete("/resumes/{resume_id}", status_code=204)
def delete_resume(resume_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user), storage: LocalStorage = Depends(get_storage)):
    resume = get_owned_or_404(db, Resume, resume_id, user)
    key = resume.storage_key
    db.delete(resume)
    record(db, "resume_deleted", user.id, resume_id=str(resume_id))
    db.commit()
    storage.delete(key)  # file goes only after the database commit succeeded
    return Response(status_code=204)


__all__ = ["not_found", "router"]
