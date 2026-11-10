import pytest
from sqlalchemy import select

from app.companies import seed
from app.llm.fake import FakeProvider
from app.models.company import Company
from app.models.user import User
from app.research import auto as auto_research
from app.research import service
from app.research.provider import BudgetedProvider, FakeResearchProvider, SearchHit
from tests.test_research import CAREERS, CAREERS_TEXT, GOOD, SITE, TECH, TECH_TEXT, analysed_resume, make_research, search_all  # noqa: F401


@pytest.fixture
def env(monkeypatch):
    state = {"research": make_research(), "llm": FakeProvider([GOOD])}
    monkeypatch.setattr(service, "build_research", lambda: state["research"])
    monkeypatch.setattr(service, "build_llm", lambda: state["llm"])
    return state


@pytest.fixture
def user(make_api):
    u = make_api()
    u.signup("user@example.com")
    return u


@pytest.fixture
def rid(user, app):
    return analysed_resume(user, app)


@pytest.fixture
def seeded(db):
    seed.import_seed(db)
    return db


def names(resp, n=4):
    return [c["name"] for c in resp.json()["companies"][:n]]


def test_recommendations_follow_the_role_family(user, rid, seeded):
    ml = user.get(f"/discover/recommendations?resume_id={rid}&role=ai-ml-engineer-intern")
    web = user.get(f"/discover/recommendations?resume_id={rid}&role=frontend-developer")
    assert ml.status_code == web.status_code == 200
    assert ml.json()["role"]["family"] == "ai-ml" and web.json()["role"]["family"] == "frontend"
    top_ml, top_web = names(ml), names(web)
    assert set(top_ml) != set(top_web)
    assert {"Afiniti", "Folio3", "Conrad Labs"} & set(top_ml)
    assert "Afiniti" not in top_web and ({"Cubix", "Tkxel", "10Pearls", "Devsinc"} & set(top_web))
    assert all(c["status"] == "candidate" and c["match"]["score"] >= 0 for c in ml.json()["companies"])  # nothing is presented as verified
    assert len(ml.json()["roles"]) == 8 and "reasons" in ml.json()["companies"][0]["match"]


def test_recommendations_need_an_analysed_resume_and_are_private(user, make_api, rid, seeded):
    other = make_api()
    other.signup("other@example.com")
    assert other.get(f"/discover/recommendations?resume_id={rid}").status_code == 404
    assert user.get(f"/discover/recommendations?resume_id={rid}&q=afiniti").json()["companies"][0]["name"] == "Afiniti"


def test_a_candidate_company_can_be_chosen_for_general_practice(user, rid, seeded, monkeypatch):
    from tests.assess_helpers import ScriptedAI
    from app.assessments import service as asvc

    monkeypatch.setattr(asvc, "build_llm", lambda: ScriptedAI())
    r = user.post("/assessments", {"resume_id": rid, "role": "python-developer", "company": "arbisoft"})
    assert r.status_code == 202
    a = user.get(f"/assessments/{r.json()['id']}").json()
    assert a["status"] == "ready" and a["mode"] == "general" and a["company"] is None and "arbisoft" in a["notice"].lower()


def test_unknown_company_is_404(user, rid, seeded):
    assert user.get("/discover/companies/nope").status_code == 404


def test_user_research_flow(env, user, db, make_api):
    admin = make_api()
    admin.signup("admin@example.com")
    db.scalars(select(User).where(User.email == "admin@example.com")).one().role = "admin"
    db.commit()
    c = admin.post("/admin/companies", {"name": "Acme Software", "website": SITE, "tech_focus": ["Python"]}).json()
    assert user.get("/companies/acme-software").status_code == 404  # still a candidate in the public directory
    r = user.post("/discover/companies/acme-software/research")
    assert r.status_code == 202
    d = user.get("/discover/companies/acme-software").json()
    assert d["status"] == "verified_lahore" and d["auto_verified"] is True
    assert d["latest_run"]["status"] == "succeeded" and d["latest_run"]["summary"]["lahore_confirmed"] is True
    assert d["requirements"] and all(x["label"] in ("official_verified", "public_candidate_report") for x in d["requirements"])
    assert d["locations"] and d["locations"][0]["address"] is None  # never an invented address
    row = db.scalars(select(Company).where(Company.slug == "acme-software")).one()
    assert row.verifications[-1].reviewer_id is None and "AUTOMATIC" in row.verifications[-1].notes
    assert user.get("/companies/acme-software").status_code == 200  # now in the public directory as well


def test_research_without_any_lahore_mention_leaves_the_company_unconfirmed(env, user, db, make_api):
    admin = make_api()
    admin.signup("admin@example.com")
    db.scalars(select(User).where(User.email == "admin@example.com")).one().role = "admin"
    db.commit()
    admin.post("/admin/companies", {"name": "Acme Software", "website": SITE})
    env["research"] = FakeResearchProvider(
        search_fn=lambda q, inc, exc: [SearchHit("Eng", TECH, "Acme builds software with Python and Docker.")] if inc else [],
        pages={TECH: "Acme builds software with Python and Docker. Our team uses Python every day."},
    )
    assert user.post("/discover/companies/acme-software/research").status_code == 202
    d = user.get("/discover/companies/acme-software").json()
    assert d["status"] == "candidate" and d["requirements"] == [] and "NOT confirmed" in d["latest_run"]["summary"]["message"]


def test_rejected_companies_are_unreachable(user, db, make_api, env):
    admin = make_api()
    admin.signup("admin@example.com")
    db.scalars(select(User).where(User.email == "admin@example.com")).one().role = "admin"
    db.commit()
    c = admin.post("/admin/companies", {"name": "Bad Co"}).json()
    assert admin.post(f"/admin/companies/{c['id']}/verification", {"decision": "rejected", "notes": "Not in Lahore at all."}).status_code == 200
    assert user.get("/discover/companies/bad-co").status_code == 404
    assert user.post("/discover/companies/bad-co/research").status_code == 404


def test_domain_discovery_matches_company_name_and_ignores_directories():
    def search(q, inc, exc):
        return [
            SearchHit("Acme on Clutch", "https://clutch.co/profile/acme-soft", "Acme Soft reviews"),
            SearchHit("Acme Soft | Software", "https://www.acmesoft.com/about", "Acme Soft is a software house in Lahore"),
        ]

    p = BudgetedProvider(FakeResearchProvider(search_fn=search), 5, 5)
    assert auto_research.discover_domain(p, "Acme Soft") == "acmesoft.com"
    p2 = BudgetedProvider(FakeResearchProvider(search_fn=lambda q, i, e: [SearchHit("Reviews", "https://clutch.co/p/x", "Acme Soft")]), 5, 5)
    assert auto_research.discover_domain(p2, "Acme Soft") is None
    p3 = BudgetedProvider(FakeResearchProvider(search_fn=lambda q, i, e: [SearchHit("Systems Limited", "https://www.systemsltd.com/", "Systems Limited, Lahore")]), 5, 5)
    assert auto_research.discover_domain(p3, "Systems Limited") == "systemsltd.com"


def test_locality_is_only_taken_from_text_never_invented():
    assert auto_research._locality("Our Lahore office is in Gulberg near the main boulevard") == "Gulberg"
    assert auto_research._locality("We have an office in Lahore.") == "Lahore"
