"""Checks that the coding problems are well-formed and that their tests have teeth. Runs TRUSTED solutions through the harness."""

import re

import pytest

from app.resumes import roles
from tests.runner.helpers import bank, run_harness
from tests.runner.mutants import MUTANTS

PROBLEMS = bank()
BY_SLUG = {p["slug"]: p for p in PROBLEMS}


def cases_of(p, hidden=None):
    out = [*p["visible_tests"], *p["hidden_tests"]] if hidden is None else (p["hidden_tests"] if hidden else p["visible_tests"])
    return [{k: v for k, v in t.items() if k != "hidden"} for t in out]


def test_bank_shape():
    assert len(PROBLEMS) >= 10 and len({p["slug"] for p in PROBLEMS}) == len(PROBLEMS)
    role_slugs = {r["slug"] for r in roles.list_roles()}
    covered = set()
    for p in PROBLEMS:
        assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", p["slug"]) and p["difficulty"] in ("easy", "medium", "hard")
        assert len(p["statement"]) > 80 and p["constraints"] and p["examples"] and p["approach"] and p["complexity"]["time"]
        assert len(p["visible_tests"]) >= 3 and len(p["hidden_tests"]) >= 6, p["slug"]
        ids = [t["id"] for t in p["visible_tests"] + p["hidden_tests"]]
        assert len(ids) == len(set(ids)) and all(t["hidden"] is False for t in p["visible_tests"]) and all(t["hidden"] is True for t in p["hidden_tests"])
        assert set(p["roles"]) <= role_slugs and p["roles"] and p["minutes"] in range(10, 61)
        assert p["signature"] in p["starter_code"] and p["entry_point"] in p["signature"]
        compile(p["starter_code"], "<starter>", "exec")
        covered |= set(p["roles"])
        for ex, v in zip(p["examples"], p["visible_tests"], strict=False):
            assert ex["args"] == v["args"] and ex["output"] == v["expected"] and ex["explanation"]
    assert covered == role_slugs  # every role has problems to practise


def test_no_hidden_test_is_just_a_copy_of_a_visible_one():
    for p in PROBLEMS:
        visible = {str([t["args"]]) for t in p["visible_tests"]}
        assert not any(str([t["args"]]) in visible for t in p["hidden_tests"]), p["slug"]


def test_request_size_stays_under_the_runner_limit():
    import json

    for p in PROBLEMS:
        assert len(json.dumps({"tests": cases_of(p)})) < 600_000, p["slug"]


@pytest.mark.parametrize("slug", [p["slug"] for p in PROBLEMS])
def test_reference_solution_passes_every_test_quickly(slug):
    p = BY_SLUG[slug]
    res = run_harness(p["reference_solution"], p["entry_point"], cases_of(p), per_test_ms=p["per_test_ms"])
    bad = [(t["id"], t["status"], t["error"]) for t in res["tests"] if t["status"] != "passed"]
    assert not bad, bad
    assert max(t["runtime_ms"] for t in res["tests"]) < p["per_test_ms"] / 4  # generous headroom for slower machines


@pytest.mark.parametrize("slug", [p["slug"] for p in PROBLEMS])
def test_the_starter_code_does_not_accidentally_pass(slug):
    p = BY_SLUG[slug]
    res = run_harness(p["starter_code"], p["entry_point"], cases_of(p))
    assert all(t["status"] == "failed" for t in res["tests"]), slug


def test_every_problem_has_wrong_solutions_to_check_against():
    assert set(MUTANTS) == set(BY_SLUG)
    assert all(len(v) >= 2 for v in MUTANTS.values())


def _mutant_cases():
    return [(slug, m["name"]) for slug, ms in MUTANTS.items() for m in ms]


@pytest.mark.parametrize("slug,name", _mutant_cases())
def test_hidden_tests_catch_every_wrong_solution(slug, name):
    p = BY_SLUG[slug]
    m = next(x for x in MUTANTS[slug] if x["name"] == name)
    limit = 1000 if m.get("slow") else p["per_test_ms"]
    res = run_harness(m["code"], p["entry_point"], cases_of(p), per_test_ms=limit)
    by_id = {t["id"]: t["status"] for t in res["tests"]}
    hidden_ids = {t["id"] for t in p["hidden_tests"]}
    assert any(s != "passed" for i, s in by_id.items() if i in hidden_ids), f"{slug}: '{name}' passes every hidden test"
    if m.get("slow"):
        assert "timeout" in by_id.values()


def test_hidden_tests_matter_most_wrong_solutions_pass_the_visible_ones():
    """If hidden tests were redundant, candidates could simply pass the examples. Check that they are not."""
    sneaky = 0
    for slug, ms in MUTANTS.items():
        p = BY_SLUG[slug]
        for m in ms:
            res = run_harness(m["code"], p["entry_point"], cases_of(p, hidden=False), per_test_ms=p["per_test_ms"])
            sneaky += all(t["status"] == "passed" for t in res["tests"])
    assert sneaky >= 8, sneaky
