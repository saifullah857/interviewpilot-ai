from datetime import timedelta

import pytest
from sqlalchemy import select

from app import cli
from app.companies import seed
from app.core.db import utcnow
from app.models.audit import AuditEvent
from app.models.company import Company, CompanyVerificationRecord
from app.models.user import User

NOTES = "Checked the official contact page; Lahore office listed."


def iso(days_ago: int = 1) -> str:
    return (utcnow() - timedelta(days=days_ago)).isoformat()


@pytest.fixture
def admin(make_api, db):
    a = make_api()
    a.signup("admin@example.com")
    db.scalars(select(User).where(User.email == "admin@example.com")).one().role = "admin"
    db.commit()
    return a


@pytest.fixture
def user(make_api):
    u = make_api()
    u.signup("user@example.com")
    return u


def new_company(admin, name="Example Software", **extra):
    r = admin.post("/admin/companies", {"name": name, **extra})
    assert r.status_code == 201, r.text
    return r.json()


def add_loc(admin, cid, locality="Gulberg", is_lahore=True, address=None):
    r = admin.post(f"/admin/companies/{cid}/locations", {"locality": locality, "is_lahore": is_lahore, "address": address})
    assert r.status_code == 201, r.text
    return r.json()


def add_src(admin, cid, url="https://example.com/contact", source_type="official_website", label="official_verified", supports=True, days_ago=1):
    r = admin.post(
        f"/admin/companies/{cid}/sources",
        {"url": url, "source_type": source_type, "label": label, "supports_lahore": supports, "excerpt": "Lists a Lahore office.", "retrieved_at": iso(days_ago)},
    )
    assert r.status_code == 201, r.text
    return r.json()["sources"][-1]["id"]


def verify(admin, cid, evidence, notes=NOTES):
    return admin.post(f"/admin/companies/{cid}/verification", {"decision": "verified", "evidence_ids": evidence, "notes": notes})


def make_verified(admin, name="Example Software", locality="Gulberg", **extra):
    c = new_company(admin, name, **extra)
    add_loc(admin, c["id"], locality)
    sid = add_src(admin, c["id"], url=f"https://{c['slug']}.example.com/contact")
    assert verify(admin, c["id"], [sid]).status_code == 200
    return c


# ---------- access control ----------
def test_directory_requires_login(api):
    assert api.get("/companies").status_code == 401
    assert api.get("/companies/localities").status_code == 401


def test_admin_endpoints_reject_normal_users_and_anonymous(user, api):
    for method, path, body in [("get", "/admin/companies", None), ("post", "/admin/companies", {"name": "X Corp"})]:
        r = getattr(user, method)(path, *([body] if body else []))
        assert r.status_code == 403 and r.json()["error"]["code"] == "forbidden"
        assert getattr(api, method)(path, *([body] if body else [])).status_code in (401, 403)
    assert api.get("/admin/companies").status_code == 401


def test_admin_writes_need_csrf(admin):
    r = admin.post("/admin/companies", {"name": "No Csrf"}, csrf=False)
    assert r.status_code == 403 and r.json()["error"]["code"] == "csrf_failed"


# ---------- Lahore-only listing ----------
def test_empty_directory(user):
    assert user.get("/companies").json() == {"items": [], "total": 0, "page": 1, "page_size": 20}


def test_candidates_are_never_listed_or_reachable(admin, user):
    c = new_company(admin, "Candidate Co")
    add_loc(admin, c["id"])
    assert c["verification_status"] == "candidate"
    assert user.get("/companies").json()["total"] == 0
    assert user.get("/companies/candidate-co").status_code == 404


def test_verified_company_is_listed_with_only_active_evidence(admin, user):
    c = new_company(admin, "Verified Co", website="https://verified.example.com", tech_focus=["Python", "Django"])
    add_loc(admin, c["id"], "Gulberg", address="Main Boulevard")
    add_loc(admin, c["id"], "Austin", is_lahore=False)
    good = add_src(admin, c["id"], url="https://verified.example.com/contact")
    add_src(admin, c["id"], url="https://verified.example.com/unreviewed", label="unverified_or_outdated", source_type="other", supports=False)
    assert verify(admin, c["id"], [good]).status_code == 200

    listing = user.get("/companies").json()
    assert listing["total"] == 1 and listing["items"][0]["localities"] == ["Gulberg"]
    assert listing["items"][0]["evidence_count"] == 1
    detail = user.get("/companies/verified-co").json()
    assert [loc["locality"] for loc in detail["locations"]] == ["Gulberg"]  # non-Lahore location never exposed
    assert [s["url"] for s in detail["sources"]] == ["https://verified.example.com/contact"]
    assert "supports_lahore" not in str(detail) and "unreviewed" not in str(detail)  # admin-only data stays private


def test_company_with_only_non_lahore_location_cannot_be_verified(admin):
    c = new_company(admin, "Overseas Only")
    add_loc(admin, c["id"], "Austin", is_lahore=False)
    sid = add_src(admin, c["id"])
    r = verify(admin, c["id"], [sid])
    assert r.status_code == 422 and r.json()["error"]["code"] == "verification_requirements_not_met"
    assert any("Lahore" in d for d in r.json()["error"]["details"])


def test_public_api_ignores_a_forced_verified_status_without_a_lahore_location(admin, user, db):
    c = new_company(admin, "Forced Overseas")
    add_loc(admin, c["id"], "Austin", is_lahore=False)
    row = db.scalars(select(Company).where(Company.slug == "forced-overseas")).one()
    row.verification_status = "verified_lahore"  # simulates bad data written around the service
    db.commit()
    assert user.get("/companies").json()["total"] == 0
    assert user.get("/companies/forced-overseas").status_code == 404


def test_rejected_and_stale_are_hidden(admin, user):
    a = make_verified(admin, "Alpha Co")
    b = make_verified(admin, "Beta Co")
    assert admin.post(f"/admin/companies/{a['id']}/verification", {"decision": "marked_stale"}).status_code == 200
    assert admin.post(f"/admin/companies/{b['id']}/verification", {"decision": "rejected", "notes": "Office could not be confirmed."}).status_code == 200
    assert user.get("/companies").json()["total"] == 0
    assert user.get("/companies/alpha-co").status_code == 404


def test_cannot_mark_unverified_company_stale(admin):
    c = new_company(admin, "Never Verified")
    assert admin.post(f"/admin/companies/{c['id']}/verification", {"decision": "marked_stale"}).status_code == 409


# ---------- verification rules ----------
def test_verification_requirements(admin):
    c = new_company(admin, "Rules Co")
    cid = c["id"]
    r = verify(admin, cid, [], notes="")
    assert r.status_code == 422 and len(r.json()["error"]["details"]) == 3  # no location, no evidence, no notes
    add_loc(admin, cid)
    weak = add_src(admin, cid, url="https://x.example.com/a", label="unverified_or_outdated", source_type="other", supports=False)
    assert verify(admin, cid, [weak]).status_code == 422  # not official
    not_lahore = add_src(admin, cid, url="https://x.example.com/b", supports=False)
    assert verify(admin, cid, [not_lahore]).status_code == 422  # official but does not support Lahore
    good = add_src(admin, cid, url="https://x.example.com/c")
    assert verify(admin, cid, [good], notes="short").status_code == 422
    assert verify(admin, cid, [good]).status_code == 200


def test_evidence_from_another_company_is_refused(admin):
    a, b = new_company(admin, "Company A"), new_company(admin, "Company B")
    add_loc(admin, a["id"])
    foreign = add_src(admin, b["id"], url="https://b.example.com/contact")
    r = verify(admin, a["id"], [foreign])
    assert r.status_code == 422 and r.json()["error"]["code"] == "unknown_evidence"


def test_verification_record_names_reviewer_and_evidence(admin, db):
    c = make_verified(admin, "Recorded Co")
    rec = db.scalars(select(CompanyVerificationRecord)).one()
    reviewer = db.scalars(select(User).where(User.email == "admin@example.com")).one()
    assert rec.reviewer_id == reviewer.id and rec.decision == "verified" and len(rec.evidence_ids) == 1
    assert db.scalars(select(Company)).one().last_verified_at is not None
    events = [e for e in db.scalars(select(AuditEvent)) if e.action == "verification_decision"]
    assert events and "admin@example.com" not in str([e.detail for e in events]) and c["id"] in str(events[0].detail)


def test_rejection_needs_an_explanation(admin):
    c = new_company(admin, "Rejected Co")
    assert admin.post(f"/admin/companies/{c['id']}/verification", {"decision": "rejected"}).status_code == 422


# ---------- source rules ----------
@pytest.mark.parametrize(
    "source_type,label", [("candidate_report", "official_verified"), ("official_website", "public_candidate_report"), ("other", "official_verified")]
)
def test_label_must_fit_source_type(admin, source_type, label):
    c = new_company(admin, "Label Co")
    r = admin.post(f"/admin/companies/{c['id']}/sources", {"url": "https://x.example.com", "source_type": source_type, "label": label, "retrieved_at": iso()})
    assert r.status_code == 422 and r.json()["error"]["code"] == "label_mismatch"


def test_ai_generated_label_cannot_be_a_research_source(admin):
    c = new_company(admin, "Ai Label Co")
    r = admin.post(
        f"/admin/companies/{c['id']}/sources", {"url": "https://x.example.com", "source_type": "other", "label": "ai_generated_practice", "retrieved_at": iso()}
    )
    assert r.status_code == 422


def test_source_validation(admin):
    c = new_company(admin, "Source Co")
    base = {"source_type": "official_website", "label": "official_verified", "retrieved_at": iso()}
    assert admin.post(f"/admin/companies/{c['id']}/sources", {**base, "url": "javascript:alert(1)"}).status_code == 422
    assert (
        admin.post(
            f"/admin/companies/{c['id']}/sources", {**base, "url": "https://x.example.com", "retrieved_at": (utcnow() + timedelta(days=30)).isoformat()}
        ).status_code
        == 422
    )
    assert admin.post(f"/admin/companies/{c['id']}/sources", {**base, "url": "https://x.example.com", "retrieved_at": "2026-01-01T00:00:00"}).status_code == 422
    assert admin.post(f"/admin/companies/{c['id']}/sources", {**base, "url": "https://x.example.com"}).status_code == 201
    assert admin.post(f"/admin/companies/{c['id']}/sources", {**base, "url": "https://x.example.com"}).status_code == 409


def test_company_validation(admin):
    assert admin.post("/admin/companies", {"name": "Bad Slug", "slug": "Bad Slug!"}).status_code == 422
    assert admin.post("/admin/companies", {"name": "Extra", "verification_status": "verified_lahore"}).status_code == 422  # cannot create pre-verified
    new_company(admin, "Dup Co")
    assert admin.post("/admin/companies", {"name": "Dup Co"}).status_code == 409


# ---------- freshness ----------
@pytest.mark.parametrize(
    "source_type,label,days,expected",
    [
        ("official_website", "official_verified", 10, "official_verified"),
        ("official_website", "official_verified", 200, "unverified_or_outdated"),
        ("job_posting", "official_verified", 40, "unverified_or_outdated"),
        ("job_posting", "official_verified", 20, "official_verified"),
        ("candidate_report", "public_candidate_report", 400, "unverified_or_outdated"),
        ("candidate_report", "public_candidate_report", 300, "public_candidate_report"),
    ],
)
def test_stale_evidence_is_relabelled(admin, user, source_type, label, days, expected):
    c = new_company(admin, "Fresh Co")
    add_loc(admin, c["id"])
    good = add_src(admin, c["id"], url="https://fresh.example.com/contact")
    extra = add_src(admin, c["id"], url="https://fresh.example.com/extra", source_type=source_type, label=label, supports=False, days_ago=days)
    assert verify(admin, c["id"], [good, extra]).status_code == 200
    src = next(s for s in user.get("/companies/fresh-co").json()["sources"] if s["id"] == extra)
    assert src["label"] == expected and src["stored_label"] == label


def test_stale_check_cli_hides_overdue_companies(admin, user, db):
    make_verified(admin, "Old Co")
    row = db.scalars(select(Company)).one()
    row.last_verified_at = utcnow() - timedelta(days=200)
    db.commit()
    assert user.get("/companies").json()["items"][0]["needs_recheck"] is True
    assert cli.main(["stale-check"]) == 0
    assert user.get("/companies").json()["total"] == 0
    db.expire_all()
    assert db.scalars(select(Company)).one().verification_status == "stale"


# ---------- search, filter, paging ----------
def test_filters_search_and_paging(admin, user):
    make_verified(admin, "Alpha Labs", locality="Gulberg", tech_focus=["Python", "PyTorch"])
    make_verified(admin, "Beta Works", locality="Johar Town", tech_focus=["Java"])
    make_verified(admin, "Gamma Data", locality="Gulberg", tech_focus=["SQL"])
    names = lambda r: [c["name"] for c in r.json()["items"]]  # noqa: E731
    assert names(user.get("/companies?locality=gulberg")) == ["Alpha Labs", "Gamma Data"]
    assert names(user.get("/companies?tech=java")) == ["Beta Works"]
    assert names(user.get("/companies?q=pytor")) == ["Alpha Labs"]
    assert names(user.get("/companies?q=beta")) == ["Beta Works"]
    assert user.get("/companies?locality=Karachi").json()["total"] == 0
    page2 = user.get("/companies?page=2&page_size=2").json()
    assert page2["total"] == 3 and [c["name"] for c in page2["items"]] == ["Gamma Data"]
    assert user.get("/companies/localities").json() == ["Gulberg", "Johar Town"]
    assert user.get("/companies?page_size=500").status_code == 422


# ---------- admin listing ----------
def test_admin_sees_candidates_and_can_filter_by_status(admin):
    new_company(admin, "Cand One")
    make_verified(admin, "Ver One")
    assert len(admin.get("/admin/companies").json()) == 2
    assert [c["name"] for c in admin.get("/admin/companies?status=candidate").json()] == ["Cand One"]


# ---------- seed + CLI ----------
def test_real_seed_file_contains_only_unverified_candidates():
    s = seed.load_seed(seed.DEFAULT_SEED)
    assert len(s.companies) >= 10
    slugs = [c.slug for c in s.companies]
    assert len(slugs) == len(set(slugs))
    assert all(not c.website and not c.sources and not c.locations for c in s.companies)  # no unsourced facts


def test_seed_import_is_idempotent_and_never_verifies(db):
    first = seed.import_seed(db)
    again = seed.import_seed(db)
    assert first["created"] >= 10 and again["created"] == 0
    assert {c.verification_status for c in db.scalars(select(Company))} == {"candidate"}


def test_reimporting_seed_does_not_touch_verification(admin, db):
    seed.import_seed(db)
    row = db.scalars(select(Company).where(Company.slug == "arbisoft")).one()
    cid = str(row.id)
    add_loc(admin, cid)
    sid = add_src(admin, cid, url="https://arbisoft.example.com/contact")
    assert verify(admin, cid, [sid]).status_code == 200
    seed.import_seed(db)
    db.expire_all()
    assert db.scalars(select(Company).where(Company.slug == "arbisoft")).one().verification_status == "verified_lahore"


def test_seed_cannot_carry_a_status(tmp_path, db):
    bad = tmp_path / "bad.json"
    bad.write_text('{"_meta": {}, "companies": [{"name": "Sneaky Co", "verification_status": "verified_lahore"}]}')
    with pytest.raises(ValueError):
        seed.import_seed(db, bad)


def test_make_admin_cli(user, db, capsys):
    assert cli.main(["make-admin", "nobody@example.com"]) == 1
    assert user.get("/admin/companies").status_code == 403
    assert cli.main(["make-admin", "USER@example.com"]) == 0
    assert user.get("/admin/companies").status_code == 200
    assert any(e.action == "admin_granted" for e in db.scalars(select(AuditEvent)))


def test_admin_can_edit_descriptive_fields_but_never_the_status(admin, user):
    c = make_verified(admin, "Editable Co")
    r = admin.patch(f"/admin/companies/{c['id']}", {"website": "https://editable.example.com", "tech_focus": [" Python ", "", "SQL"], "description": "Builds software."})
    assert r.status_code == 200 and r.json()["tech_focus"] == ["Python", "SQL"] and r.json()["verification_status"] == "verified_lahore"
    assert user.get("/companies/editable-co").json()["website"] == "https://editable.example.com/"
    for bad in ({"verification_status": "candidate"}, {"website": "javascript:alert(1)"}, {"tech_focus": ["x" * 41]}):
        assert admin.patch(f"/admin/companies/{c['id']}", bad).status_code == 422
    assert user.patch(f"/admin/companies/{c['id']}", {"description": "hack"}).status_code == 403
    assert admin.patch(f"/admin/companies/{c['id']}", {"website": None}).json()["website"] is None
