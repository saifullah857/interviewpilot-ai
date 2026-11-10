import secrets

from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.assessments.routes import router as assessments_router
from app.auth import cookies
from app.auth.routes import router as auth_router
from app.readiness.routes import router as readiness_router
from app.screening.routes import router as screening_router
from app.questions.routes import admin as admin_questions_router, router as questions_router
from app.coding.routes import router as coding_router
from app.companies.routes import admin as admin_companies_router
from app.companies.routes import router as companies_router
from app.core.config import get_settings
from app.core.db import get_db
from app.core.errors import AppError, install_error_handlers
from app.core.nul_guard import RejectNul
from app.discover.routes import router as discover_router
from app.interviews.routes import router as interviews_router
from app.reports.routes import router as reports_router
from app.research.routes import router as research_router
from app.resumes.routes import router as resumes_router
from app.users.routes import router as me_router

UNSAFE = {"POST", "PUT", "PATCH", "DELETE"}

api = APIRouter(prefix="/api/v1")


@api.get("/health", tags=["health"])
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("select 1"))
    except Exception:
        return JSONResponse({"status": "degraded", "database": "unavailable"}, status_code=503)
    return {"status": "ok", "database": "ok"}


api.include_router(auth_router)
api.include_router(me_router)
api.include_router(resumes_router)
api.include_router(assessments_router)
api.include_router(coding_router)
api.include_router(questions_router)
api.include_router(screening_router)
api.include_router(readiness_router)
api.include_router(admin_questions_router)
api.include_router(interviews_router)
api.include_router(reports_router)
api.include_router(companies_router)
api.include_router(admin_companies_router)
api.include_router(research_router)
api.include_router(discover_router)


def create_app() -> FastAPI:
    s = get_settings()
    dev = s.app_env == "development"  # API docs are only exposed in development
    app = FastAPI(
        title="InterviewPilot AI API",
        version="0.2.0",
        docs_url="/docs" if dev else None,
        redoc_url=None,
        openapi_url="/openapi.json" if dev else None,
    )
    install_error_handlers(app)
    app.add_middleware(RejectNul)  # innermost: runs after the CSRF check, and its answers still get the security headers

    @app.middleware("http")
    async def csrf_guard(request: Request, call_next):
        # Double-submit token: the X-CSRF-Token header must equal the ip_csrf cookie on every state-changing call.
        if request.method in UNSAFE and request.url.path.startswith("/api/"):
            header, cookie = request.headers.get("x-csrf-token", ""), request.cookies.get(cookies.CSRF, "")
            if not header or not cookie or not secrets.compare_digest(header, cookie):
                err = AppError(403, "csrf_failed", "Security check failed. Reload the page and try again.")
                return JSONResponse(err.body(), status_code=403)
        return await call_next(request)

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        resp = await call_next(request)
        # The API only returns JSON: it must never be framed, sniffed, cached by a shared cache, or treated as a page.
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "no-referrer")
        resp.headers.setdefault("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
        if request.url.path.startswith("/api/"):
            resp.headers.setdefault("Cache-Control", "no-store")
        if s.app_env == "production":
            resp.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return resp

    app.include_router(api)
    # Added last so it is outermost and also decorates CSRF rejections.
    app.add_middleware(CORSMiddleware, allow_origins=s.cors_list, allow_credentials=True,
                       allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"], allow_headers=["Content-Type", "X-CSRF-Token"])
    return app


app = create_app()
