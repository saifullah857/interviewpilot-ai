"""Company-focused and resume-shaped coding sessions, automatic reports, the progress dashboard, and a real (not scripted) run."""

import pytest

from app.coding import focus
from app.coding import problems as bank_mod
from app.coding.routes import runner_dep
from app.coding.runner_client import LocalRunnerClient
from app.resumes import roles
from tests.coding_helpers import ScriptedRunner
from tests.test_assessments import analysed_resume


@pytest.fixture
def bank(db):
    bank_mod.import_bank(db)
    return db


@pytest.fixture
def user(make_api):
    u = make_api()
    u.signup("user@example.com")
    return u


@pytest.fixture
def runner(app):
    r = ScriptedRunner()
    app.dependency_overrides[runner_dep] = lambda: r
    return r


def test_the_bank_has_screening_problems_that_combine_structures(bank, user):
    allp = user.get("/coding/problems").json()
    assert len(allp) >= 38
    combo = [p for p in allp if len(set(p["ds"]) & {"list", "tuple", "dict", "set"}) >= 3]
    assert len(combo) >= 8 and all("loop" in p["ds"] or "condition" in p["ds"] for p in combo)
    for structure in ("list", "tuple", "dict", "set"):
        assert any(structure in p["ds"] for p in allp), structure


def test_company_list_is_honest_about_what_focus_means(user):
    d = user.get("/coding/companies").json()
    assert d["companies"] and "not the company's real interview questions" in d["disclaimer"]
    assert all(c["label"] == "practice_focus_not_verified" and c["focus_tags"] for c in d["companies"])


def test_a_company_focus_changes_which_problems_are_chosen_and_says_why(bank, user, runner):
    seen = {}
    for slug in ("netsol-technologies", "folio3"):
        r = user.post("/coding/sessions", {"role": "python-developer", "count": 3, "company": slug})
        assert r.status_code == 201, r.text
        d = r.json()
        assert d["company"]["slug"] == slug and d["company"]["label"] == "practice_focus_not_verified"
        assert set(d["plan"]["reasons"]) == {p["slug"] for p in d["problems"]} and all(d["plan"]["reasons"].values())
        seen[slug] = d
        user.post(f"/coding/sessions/{d['id']}/finish")
    w = focus.company_weights("netsol-technologies")
    assert w["fintech"] > 0 and focus.company_weights("folio3")["fintech"] == 0
    assert user.post("/coding/sessions", {"role": "python-developer", "company": "no-such-house"}).status_code == 404


def test_resume_skills_pick_the_language_and_say_when_it_cannot_run_it(bank, user, runner, app):
    rid = analysed_resume(user, app)
    d = user.post("/coding/sessions", {"role": "python-developer", "count": 3, "resume_id": rid}).json()
    assert d["language"] == "python" and d["plan"]["resume"] is not None and d["plan"]["language"] == "python"
    user.post(f"/coding/sessions/{d['id']}/finish")
    assert user.post("/coding/sessions", {"role": "python-developer", "resume_id": "00000000-0000-0000-0000-000000000000"}).status_code == 404


def test_language_note_when_the_resume_language_is_not_runnable():
    from app.resumes.schemas import ParsedResume

    parsed = ParsedResume.model_validate({"skills": [{"name": "Java", "category": "language", "source": "stated"}]})
    rp = focus.resume_profile(parsed)
    assert rp["language"] == "python" and "java" in rp["language_note"].lower()


def test_finishing_a_session_saves_an_automatic_report_with_the_coding_score(bank, user, runner):
    d = user.post("/coding/sessions", {"role": "python-developer", "count": 2}).json()
    sid, first = d["id"], d["problems"][0]["slug"]
    assert user.post(f"/coding/sessions/{sid}/submit", {"problem": first, "code": "PASS_ALL"}).status_code == 200
    fin = user.post(f"/coding/sessions/{sid}/finish")
    assert fin.status_code == 200
    listing = user.get("/reports").json()
    assert len(listing) == 1 and listing[0]["auto"] is True and "coding_correctness" in listing[0]["included"]
    rep = user.get(f"/reports/{listing[0]['id']}").json()
    by = {c["key"]: c for c in rep["components"]}
    assert by["coding_correctness"]["status"] == "available" and by["coding_correctness"]["value"] > 0
    assert user.post(f"/coding/sessions/{sid}/finish").status_code in (200, 409) and len(user.get("/reports").json()) == 1  # no duplicate


def test_dashboard_has_the_data_for_every_graph(bank, user, runner):
    empty = user.get("/reports/dashboard").json()
    assert empty["summary"]["coding_sessions"] == 0 and empty["coding"] == [] and empty["reports"] == []
    d = user.post("/coding/sessions", {"role": "python-developer", "count": 2}).json()
    for p in d["problems"]:
        user.post(f"/coding/sessions/{d['id']}/submit", {"problem": p["slug"], "code": "PASS_ALL"})
    user.post(f"/coding/sessions/{d['id']}/finish")
    dash = user.get("/reports/dashboard").json()
    s = dash["summary"]
    assert s["coding_sessions"] == 1 and s["problems_solved"] == 2 and s["average_coding_score"] == 100 and s["reports"] == 1
    c = dash["coding"][0]
    assert c["score"] == 100 and c["solved"] == 2 and len(c["problems"]) == 2 and dash["topics"] and dash["difficulty"] and dash["structures"]
    assert len(dash["reports"]) == 1 and dash["reports"][0]["auto"] is True


def test_dashboard_is_private(bank, user, make_api, runner):
    other = make_api()
    other.signup("other@example.com")
    d = user.post("/coding/sessions", {"role": "python-developer", "count": 1}).json()
    user.post(f"/coding/sessions/{d['id']}/submit", {"problem": d["problems"][0]["slug"], "code": "PASS_ALL"})
    user.post(f"/coding/sessions/{d['id']}/finish")
    assert other.get("/reports/dashboard").json()["summary"]["coding_sessions"] == 0


def test_a_real_submission_runs_and_counts_with_the_built_in_runner(bank, user, app):
    """No scripted double here: the code really runs in a child Python process and the score really counts."""
    app.dependency_overrides[runner_dep] = lambda: LocalRunnerClient()
    assert user.get("/coding/runner").json()["executes_code"] is True
    d = user.post("/coding/sessions", {"problem_slugs": ["unique-keep-order"]}).json()
    good = "def unique_keep_order(items):\n    seen = set()\n    out = []\n    for x in items:\n        if x not in seen:\n            seen.add(x)\n            out.append(x)\n    return out\n"
    bad = "def unique_keep_order(items):\n    return sorted(set(items))\n"
    sub = user.post(f"/coding/sessions/{d['id']}/submit", {"problem": "unique-keep-order", "code": bad}).json()
    assert sub["executed"] is True and sub["passed_count"] < sub["total_count"]
    sub = user.post(f"/coding/sessions/{d['id']}/submit", {"problem": "unique-keep-order", "code": good}).json()
    assert sub["executed"] is True and sub["passed_count"] == sub["total_count"]
    user.post(f"/coding/sessions/{d['id']}/finish")
    rows = user.get("/coding/sessions").json()
    assert rows[0]["score"] == 100 and rows[0]["solved"] == 1 and rows[0]["executed"] is True


def test_roles_module_still_exposes_what_focus_needs():
    assert hasattr(roles, "canon") and hasattr(roles, "_resume_skills")
