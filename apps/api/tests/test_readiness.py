import pytest

from app.coding.routes import runner_dep
from app.questions import service as qs
from app.readiness import engine
from tests.coding_helpers import ScriptedRunner
from tests.test_assessments import analysed_resume


@pytest.fixture
def seeded(db):
    from app.coding import problems as bank

    bank.import_bank(db)
    qs.import_bank(db)


@pytest.fixture
def user(make_api):
    u = make_api()
    u.signup("ready@example.com")
    return u


def _screen(user, db, role="python-developer", level="easy", count=10, right=True):
    from app.models.question import BankQuestion

    d = user.post("/screening/sessions", {"role": role, "level": level, "count": count}).json()
    qmap = {q.slug: q for q in db.query(BankQuestion).filter(BankQuestion.slug.in_([x["slug"] for x in d["questions"]]))}
    for q in d["questions"]:
        wrong = (qmap[q["slug"]].answer_index + 1) % len(q["options"])
        user.put(f"/screening/sessions/{d['id']}/answers", {"question": q["slug"], "choice": qmap[q["slug"]].answer_index if right else wrong})
    user.post(f"/screening/sessions/{d['id']}/submit")


def test_with_no_work_done_nothing_is_claimed(seeded, user):
    r = user.get("/readiness", params={"role": "python-developer", "company": "arbisoft"}).json()
    assert r["evidence_count"] == 0 and r["overall"]["value"] is None  # no resume and no results: no number at all
    assert r["overall"]["label"] == "Not enough data" and r["overall"]["confidence"] == "resume_only"
    by = {c["key"]: c for c in r["components"]}
    assert by["screening"]["status"] == "not_assessed" and by["coding_correctness"]["status"] == "not_assessed" and by["skill_match"]["status"] == "not_assessed"
    assert all(c["effective_weight"] == 0 for c in r["components"]) or by["screening"]["effective_weight"] == 0
    assert all(g["status"] in ("resume_only", "not_shown") for g in r["skill_gap"])  # no skill is called good or weak without evidence
    assert "not a hiring probability" in r["disclaimer"].lower()


def test_a_resume_alone_gives_a_labelled_estimate_not_a_match(seeded, user, app):
    rid = analysed_resume(user, app)
    r = user.get("/readiness", params={"role": "python-developer", "company": "arbisoft", "resume_id": rid}).json()
    assert r["evidence_count"] == 0 and r["overall"]["value"] is not None and r["overall"]["label"] == "Resume-based estimate only"
    assert {g["status"] for g in r["skill_gap"]} <= {"resume_only", "not_shown"}


def test_unknown_role_or_company_is_404_and_it_needs_login(seeded, user, make_api):
    assert user.get("/readiness", params={"role": "nope"}).status_code == 404
    assert user.get("/readiness", params={"role": "python-developer", "company": "nope"}).status_code == 404
    assert user.get("/readiness/companies", params={"role": "nope"}).status_code == 404
    assert user.get("/readiness/roles", params={"company": "nope"}).status_code == 404
    anon = make_api()
    assert anon.get("/readiness", params={"role": "python-developer"}).status_code in (401, 403)


def test_score_is_the_weighted_average_of_the_parts_that_have_data(seeded, user, db, app):
    rid = analysed_resume(user, app)
    _screen(user, db, right=True)
    r = user.get("/readiness", params={"role": "python-developer", "company": "arbisoft", "resume_id": rid}).json()
    parts = [c for c in r["components"] if c["value"] is not None]
    assert {c["key"] for c in parts} == {"skill_match", "role_relevance", "screening"} and r["evidence_count"] == 1
    expected = round(sum(c["value"] * c["weight"] for c in parts) / sum(c["weight"] for c in parts))
    assert r["overall"]["value"] == expected
    wsum = sum(c["weight"] for c in parts)
    assert all(c["effective_weight"] == round(100 * c["weight"] / wsum) for c in parts)
    assert next(c for c in r["components"] if c["key"] == "coding_correctness")["effective_weight"] == 0  # a part without data carries no weight
    assert next(c for c in parts if c["key"] == "screening")["value"] == 100 and r["overall"]["confidence"] == "limited"
    assert r["overall"]["label"] != "Resume-based estimate only"


def test_a_wrong_screening_lowers_the_score_and_creates_assessed_weak_skills(seeded, user, db, app):
    rid = analysed_resume(user, app)
    _screen(user, db, right=True, count=10)
    good = user.get("/readiness", params={"role": "python-developer", "resume_id": rid}).json()["overall"]["value"]
    # finish and start another test where every answer is wrong
    _screen(user, db, right=False, count=10, level="easy")
    _screen(user, db, right=False, count=10, level="easy")
    r = user.get("/readiness", params={"role": "python-developer", "resume_id": rid}).json()
    scr = next(c for c in r["components"] if c["key"] == "screening")
    assert scr["value"] == round((100 + 0 + 0) / 3) and r["overall"]["value"] < good
    statuses = {g["skill"]: g for g in r["skill_gap"]}
    assert statuses["python"]["status"] in ("weak", "improve") and statuses["python"]["evidence_source"] == "screening" and statuses["python"]["score"] is not None
    assert any(a["type"] == "screening" and a["params"]["role"] == "python-developer" for a in r["next_actions"])
    assert r["suggested_questions"] and all("slug" in q for q in r["suggested_questions"]) and len(r["suggested_coding"]) == 3


def test_company_focus_changes_the_match_and_the_company_table_is_sorted(seeded, user, app):
    rid = analysed_resume(user, app)
    fin = engine.role_relevance(engine._catalog_role("backend-developer"), "netsol-technologies")
    game = engine.role_relevance(engine._catalog_role("backend-developer"), "mindstorm-studios")
    assert fin is not None and game is not None and fin != game
    t = user.get("/readiness/companies", params={"role": "python-developer", "resume_id": rid}).json()
    assert len(t["items"]) == 21 and "not the company's real interview questions" in t["focus_note"]
    vals = [i["value"] for i in t["items"]]
    assert vals == sorted(vals, reverse=True) and len(set(vals)) > 1  # not the same number for everyone
    assert all(i["matching_skills"] is not None for i in t["items"])


def test_role_table_covers_all_roles_and_never_labels_a_resume_only_estimate_as_a_match(seeded, user, app):
    rid = analysed_resume(user, app)
    t = user.get("/readiness/roles", params={"resume_id": rid}).json()
    assert len(t["items"]) == 8 and t["has_resume"] is True
    assert all(i["label"] == "Resume-based estimate only" for i in t["items"] if i["evidence_count"] == 0)


def test_coding_results_are_part_of_readiness(seeded, user, db, app):
    r = ScriptedRunner()
    app.dependency_overrides[runner_dep] = lambda: r
    d = user.post("/coding/sessions", {"role": "python-developer", "count": 1}).json()
    user.post(f"/coding/sessions/{d['id']}/submit", {"problem": d["problems"][0]["slug"], "code": "PASS_ALL"})
    user.post(f"/coding/sessions/{d['id']}/finish")
    res = user.get("/readiness", params={"role": "python-developer"}).json()
    cod = next(c for c in res["components"] if c["key"] == "coding_correctness")
    assert cod["status"] == "available" and cod["value"] == 100 and res["evidence_count"] >= 1
