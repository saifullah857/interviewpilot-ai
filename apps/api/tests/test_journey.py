"""Phase 10: the whole product journey through the public API, with scripted AI and runner doubles (no network, no real model)."""

import uuid

from sqlalchemy import func, select, text

from app.core.db import Base
from app.models.assessment import AssessmentQuestion
from app.models.audit import AuditEvent
from app.models.interview import InterviewTurn
from tests.conftest import STORAGE_DIR
from tests.test_assessments import add_evidence, admin, analysed_resume, started, verified_company  # noqa: F401 (admin is a fixture)
from tests.test_reports import ROLE, ai, bank, coding_session, evaluated_interview, make, other, planner, rid, runner, submitted_assessment, user  # noqa: F401 (fixtures)

PASSWORD = "correct horse battery"
OFFICIAL = "official_verified"


def test_the_whole_journey_from_signup_to_a_company_report_and_back_to_nothing(user, other, admin, app, db, bank, runner, ai, planner, monkeypatch):  # noqa: F811
    # ---- a verified Lahore company with approved evidence, and a candidate that must stay invisible
    acme = verified_company(admin)
    add_evidence(db, acme["id"])
    add_evidence(db, acme["id"], status="unreviewed", url="https://acme.example.com/rumour")  # unapproved: must never surface anywhere
    ghost = admin.post("/admin/companies", {"name": "Ghost Overseas Ltd"}).json()
    listed = {c["slug"] for c in user.get("/companies").json()["items"]}
    assert acme["slug"] in listed and ghost["slug"] not in listed
    assert user.get(f"/companies/{ghost['slug']}").status_code == 404
    assert admin.post(f"/admin/companies/{ghost['id']}/verification", {"decision": "rejected", "notes": "Not in Lahore at all."}).status_code == 200

    # ---- resume: upload, analyse, fit against the role and the company
    res_id = analysed_resume(user, app)
    fit = user.get(f"/resumes/{res_id}/fit?role={ROLE}&company={acme['slug']}")
    assert fit.status_code == 200 and fit.json()["required"]["matched"] is not None and "company" in fit.json()
    assert user.get(f"/resumes/{res_id}/fit?role={ROLE}&company={ghost['slug']}").status_code == 404

    # ---- an unverified (non-Lahore-verified) company cannot be chosen anywhere
    assert user.post("/assessments", {"resume_id": res_id, "role": ROLE, "company": ghost["slug"]}).status_code == 404
    assert user.post("/interviews", {"resume_id": res_id, "role": ROLE, "company": ghost["slug"], "consent": True}).status_code == 404

    # ---- company assessment: labelled practice, evidence from approved sources only, objective MCQ scoring
    aid = submitted_assessment(user, res_id, db, correct=False, company=acme["slug"])
    qs = db.scalars(select(AssessmentQuestion).where(AssessmentQuestion.assessment_id == uuid.UUID(aid))).all()
    assert qs and all(q.label == "ai_generated_practice" for q in qs)
    cited = {r["url"] for q in qs for r in (q.informed_by or [])}
    assert cited <= {"https://acme.example.com/careers"} and "https://acme.example.com/rumour" not in cited

    # ---- coding: scripted runner executes, hidden tests stay hidden
    sid = coding_session(user, "FAIL_HIDDEN")
    assert user.get(f"/coding/sessions/{sid}/review").status_code == 200  # hidden-test secrecy has its own detailed tests in test_coding

    # ---- voice interview: consent, follow-ups, feedback
    iid = evaluated_interview(user, res_id, monkeypatch, answers=3, company=acme["slug"], save_transcript=True)
    turns = db.scalars(select(InterviewTurn).where(InterviewTurn.session_id == uuid.UUID(iid))).all()
    assert any(t.speaker == "interviewer" for t in turns)
    iv = user.get(f"/interviews/{iid}").json()
    assert iv["mode"] == "company" and iv["label"] == "ai_generated_practice"
    assert all(r["label"] == OFFICIAL and r["url"].endswith("/careers") for t in iv["turns"] for r in t["informed_by"])

    # ---- report that combines everything
    src = user.get(f"/reports/sources?role={ROLE}").json()
    assert [a["id"] for a in src["assessments"]] == [aid] and [c["id"] for c in src["coding_sessions"]] == [sid] and [i["id"] for i in src["interviews"]] == [iid]
    rep = make(user, resume_id=res_id, assessment_id=aid, coding_session_id=sid, interview_id=iid, horizon=7).json()
    assert rep["mode"] == "company" and rep["company"]["slug"] == acme["slug"]
    by = {c["key"]: c for c in rep["components"]}
    assert by["technical_knowledge"]["value"] == 0 and by["technical_knowledge"]["kind"] == "objective"
    assert by["coding_correctness"]["status"] == "available" and 0 < by["coding_correctness"]["value"] < 100 and by["coding_correctness"]["kind"] == "objective"
    assert by["interview_performance"]["kind"] == "subjective" and by["interview_performance"]["value"] == 62
    assert set(rep["overall"]["included"]) == {"technical_knowledge", "coding_correctness", "interview_performance"} and rep["overall"]["missing"] == []
    assert rep["overall"]["value"] == round((0.35 * 0 + 0.35 * by["coding_correctness"]["value"] + 0.30 * 62) / 1.0)
    assert [s["url"] for s in rep["sources"]] == ["https://acme.example.com/careers"] and rep["sources"][0]["label"] == OFFICIAL
    assert rep["gaps"] and rep["roadmap"]["items"] and all(p["label"] == "ai_generated_practice" for p in rep["practice_questions"])
    assert "not guarantees of selection or hiring" in rep["disclaimer"]

    # ---- a second attempt shows progress and a comparison
    aid2 = submitted_assessment(user, res_id, db, correct=True, company=acme["slug"])
    rep2 = make(user, resume_id=res_id, assessment_id=aid2, coding_session_id=sid, interview_id=iid, horizon=30).json()
    # finishing work also saves automatic reports (auto=True) into the history, so the comparison is with the closest earlier report
    listing = user.get("/reports").json()
    assert listing[0]["id"] == rep2["id"] and rep["id"] in [r["id"] for r in listing]
    assert any(r["auto"] for r in listing) and not rep["auto"]
    assert rep2["previous"] is not None and rep2["previous"]["overall_delta"] is not None
    assert rep2["roadmap"]["horizon"] == 30
    prog = user.get("/reports/progress").json()
    assert len(prog["series"]) == len(listing) and prog["latest_change"] == rep2["previous"]["overall_delta"]

    # ---- nobody else can reach any of it by changing an id
    for path in (f"/resumes/{res_id}", f"/assessments/{aid}", f"/coding/sessions/{sid}", f"/interviews/{iid}", f"/interviews/{iid}/review", f"/reports/{rep['id']}", f"/resumes/{res_id}/fit?role={ROLE}"):
        assert other.get(path).status_code == 404, path
    assert other.post("/reports", {"role": ROLE, "assessment_id": aid}).status_code == 404
    assert other.post(f"/assessments/{aid}/submit").status_code == 404
    for listing in ("/resumes", "/assessments", "/coding/sessions", "/interviews", "/reports"):
        assert other.get(listing).json() == [], listing

    # ---- leaving: deleting the account removes every user-owned row and file
    uid = user.get("/me").json()["id"]
    assert STORAGE_DIR.exists() and any(STORAGE_DIR.iterdir())
    assert user.delete("/me", {"password": PASSWORD}).status_code == 204
    from sqlalchemy.orm import Session

    from app.core.db import get_engine

    with Session(get_engine()) as s:
        from sqlalchemy import inspect

        real = set(inspect(s.get_bind()).get_table_names())  # other test modules register throw-away tables that are not in the database
        owned = [t for t in Base.metadata.sorted_tables if "user_id" in t.c and t.name in real]
        assert {t.name for t in owned} >= {"resumes", "assessments", "coding_sessions", "interview_sessions", "reports", "user_profiles", "refresh_tokens"}
        for t in owned:
            n = s.execute(text(f'SELECT count(*) FROM "{t.name}" WHERE user_id = :u'), {"u": uuid.UUID(uid).hex if s.bind.dialect.name == "sqlite" else uid}).scalar()
            assert n == 0, f"{t.name} still holds {n} row(s) of the deleted user"
        for child in ("resume_versions", "assessment_questions", "assessment_answers", "coding_submissions", "interview_turns"):  # no user_id column: they must go with their parent
            assert s.execute(text(f'SELECT count(*) FROM "{child}"')).scalar() == 0, child
        assert s.scalar(select(func.count()).select_from(AuditEvent).where(AuditEvent.actor_id == uuid.UUID(uid))) == 0
    assert not any(STORAGE_DIR.iterdir())  # the uploaded resume file is gone
    assert other.get("/me").status_code == 200  # the other user is untouched
    assert admin.get(f"/companies/{acme['slug']}").status_code == 200  # shared company data is not user data


def test_practice_without_a_company_is_labelled_general_everywhere(user, rid, ai, planner, db, monkeypatch):  # noqa: F811
    aid = submitted_assessment(user, rid, db, correct=True)
    iid = evaluated_interview(user, rid, monkeypatch)
    assert user.get(f"/assessments/{aid}").json()["mode"] == "general"
    assert user.get(f"/interviews/{iid}").json()["mode"] == "general"
    rep = make(user, assessment_id=aid, interview_id=iid).json()
    assert rep["mode"] == "general" and rep["company"] is None and rep["sources"] == []


def test_a_report_with_only_part_of_the_journey_is_honest_about_the_rest(user, rid, ai, planner, db):  # noqa: F811
    aid = submitted_assessment(user, rid, db, correct=True)
    rep = make(user, assessment_id=aid).json()
    assert {m["key"] for m in rep["overall"]["missing"]} == {"coding_correctness", "interview_performance"}
    assert rep["overall"]["limited"] is True and "1 of 3" in rep["overall"]["note"]
