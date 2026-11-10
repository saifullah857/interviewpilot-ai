import pytest

from app.coding import focus
from app.coding import problems as bank_mod
from app.coding.routes import runner_dep
from tests.coding_helpers import ScriptedRunner


@pytest.fixture
def seeded(db):
    bank_mod.import_bank(db)


@pytest.fixture
def user(make_api):
    u = make_api()
    u.signup("setter@example.com")
    return u


@pytest.fixture
def runner(app):
    r = ScriptedRunner()
    app.dependency_overrides[runner_dep] = lambda: r
    return r


def test_the_bank_has_enough_problems_of_every_level(seeded, user):
    allp = user.get("/coding/problems").json()
    counts = {d: sum(1 for p in allp if p["difficulty"] == d) for d in ("easy", "medium", "hard")}
    assert len(allp) == 62 and counts["easy"] >= 10 and counts["medium"] >= 10 and counts["hard"] >= 5


def test_every_company_gets_25_distinct_problems_with_the_10_10_5_mix(seeded, user):
    sets = {}
    for c in user.get("/coding/companies").json()["companies"]:
        r = user.get(f"/coding/companies/{c['slug']}/set")
        assert r.status_code == 200, c["slug"]
        d = r.json()
        slugs = [p["slug"] for p in d["problems"]]
        assert d["total"] == 25 and len(set(slugs)) == 25, c["slug"]
        assert d["counts"] == {"easy": 10, "medium": 10, "hard": 5}, c["slug"]
        assert [p["difficulty"] for p in d["problems"]] == ["easy"] * 10 + ["medium"] * 10 + ["hard"] * 5
        assert d["company"]["label"] == "practice_focus_not_verified" and d["solved"] == 0
        sets[c["slug"]] = frozenset(slugs)
    assert len(set(sets.values())) > 5  # companies with different focus do not all get the same set


def test_the_set_is_deterministic_and_follows_the_company_focus(seeded, user):
    a = [p["slug"] for p in user.get("/coding/companies/netsol-technologies/set").json()["problems"]]
    b = [p["slug"] for p in user.get("/coding/companies/netsol-technologies/set").json()["problems"]]
    assert a == b
    fin = {p["slug"] for p in user.get("/coding/companies/netsol-technologies/set").json()["problems"]}
    game = {p["slug"] for p in user.get("/coding/companies/mindstorm-studios/set").json()["problems"]}
    assert "bank-ledger" in fin and fin != game  # fintech focus brings the ledger problem
    assert "n-queens-count" in game or "word-ladder-length" in game  # game focus brings backtracking or graph problems


def test_a_role_filter_keeps_only_problems_for_that_role(seeded, user):
    d = user.get("/coding/companies/arbisoft/set", params={"role": "python-developer"}).json()
    assert d["total"] == 25 and d["role"] == "python-developer"
    assert user.get("/coding/companies/arbisoft/set", params={"role": "nope"}).status_code == 404
    assert user.get("/coding/companies/nope/set").status_code == 404


def test_a_session_from_the_set_skips_problems_already_solved(seeded, user, runner):
    first = user.post("/coding/sessions", {"role": "python-developer", "company": "arbisoft", "company_set": True, "count": 3}).json()
    in_set = {p["slug"] for p in user.get("/coding/companies/arbisoft/set", params={"role": "python-developer"}).json()["problems"]}
    assert {p["slug"] for p in first["problems"]} <= in_set and len(first["problems"]) == 3
    for p in first["problems"]:
        assert user.post(f"/coding/sessions/{first['id']}/submit", {"problem": p["slug"], "code": "PASS_ALL"}).status_code == 200
    user.post(f"/coding/sessions/{first['id']}/finish")
    view = user.get("/coding/companies/arbisoft/set", params={"role": "python-developer"}).json()
    assert view["solved"] == 3 and {p["slug"] for p in view["problems"] if p["solved"]} == {p["slug"] for p in first["problems"]}
    second = user.post("/coding/sessions", {"role": "python-developer", "company": "arbisoft", "company_set": True, "count": 3}).json()
    assert not ({p["slug"] for p in second["problems"]} & {p["slug"] for p in first["problems"]})
    assert second["plan"]["from_set"] is True


def test_company_set_needs_a_role_and_a_company(seeded, user):
    assert user.post("/coding/sessions", {"role": "python-developer", "company_set": True}).status_code == 422
    assert user.post("/coding/sessions", {"problem_slugs": ["two-sum"], "company_set": True}).status_code == 422


def test_unused_function_company_set_is_stable_for_unknown_slug():
    assert focus.company_set([], "nope") == []
