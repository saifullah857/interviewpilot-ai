import json
import subprocess
import sys
from datetime import timedelta

import pytest

from app.core.db import utcnow
from app.models.question import BankQuestion
from app.models.screening import ScreeningSession
from app.questions import service as qs


@pytest.fixture
def bank(db):
    return qs.import_bank(db)


@pytest.fixture
def user(make_api):
    u = make_api()
    u.signup("taker@example.com")
    return u


def test_screening_questions_are_valid_and_every_output_answer_really_is_what_the_code_prints(bank, db):
    rows = db.query(BankQuestion).filter(BankQuestion.kind.in_(["mcq", "output"])).all()
    assert len(rows) == 105 and {r.kind for r in rows} == {"mcq", "output"}
    assert {"python", "sql", "logic", "javascript", "ml"} <= {r.category for r in rows}
    checked = 0
    for r in rows:
        assert r.options[r.answer_index] and len(set(r.options)) == len(r.options) and r.explanation
        if r.kind == "output" and r.category == "python":
            code = r.prompt.split("```python\n")[1].split("\n```")[0]
            out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=10).stdout.strip()
            assert out == r.options[r.answer_index], r.slug
            checked += 1
    assert checked >= 15


def test_starting_a_test_hides_the_answers_and_respects_company_role_and_level(bank, user):
    r = user.post("/screening/sessions", {"role": "junior-ai-engineer", "company": "xeven-solutions", "level": "mixed", "count": 12})
    assert r.status_code == 201, r.text
    d = r.json()
    assert d["total"] == 12 and len(d["questions"]) == 12 and d["company"]["slug"] == "xeven-solutions" and d["status"] == "in_progress"
    assert all(q["kind"] in ("mcq", "output") and "answer_index" not in q and "explanation" not in q for q in d["questions"])
    assert all("junior-ai-engineer" in q["roles"] and "xeven-solutions" in q["companies"] for q in d["questions"])
    assert {q["difficulty"] for q in d["questions"]} >= {"easy", "medium"}
    assert user.post("/screening/sessions", {"role": "junior-ai-engineer"}).status_code == 409  # one test at a time


def test_unknown_role_company_and_tiny_pools_are_rejected(bank, user, db):
    assert user.post("/screening/sessions", {"role": "no-such-role"}).status_code == 404
    assert user.post("/screening/sessions", {"role": "python-developer", "company": "no-such"}).status_code == 404
    assert user.post("/screening/sessions", {"role": "python-developer", "count": 3}).status_code == 422
    # fewer than five enabled screening questions is refused instead of giving a tiny test
    for q in db.query(BankQuestion).filter(BankQuestion.kind.in_(["mcq", "output"])).all()[4:]:
        q.enabled = False
    db.commit()
    assert user.post("/screening/sessions", {"role": "python-developer"}).status_code == 409


def _finish(user, d, db, pick):
    qmap = {q.slug: q for q in db.query(BankQuestion).filter(BankQuestion.slug.in_([x["slug"] for x in d["questions"]]))}
    for q in d["questions"]:
        choice = pick(qmap[q["slug"]])
        if choice is not None:
            assert user.put(f"/screening/sessions/{d['id']}/answers", {"question": q["slug"], "choice": choice}).status_code == 200
    return qmap


def test_scoring_review_and_adaptive_advice(bank, user, db):
    d = user.post("/screening/sessions", {"role": "python-developer", "level": "easy", "count": 10}).json()
    _finish(user, d, db, lambda q: q.answer_index)
    res = user.post(f"/screening/sessions/{d['id']}/submit").json()
    assert res["session"]["score"] == 100 and res["session"]["correct"] == 10 and res["next_step"]["next_level"] == "medium"
    assert all(i["correct"] for i in res["review"]) and all(i["explanation"] for i in res["review"])
    assert sum(c["total"] for c in res["by_category"]) == 10
    again = user.get(f"/screening/sessions/{d['id']}/review").json()
    assert again["session"]["score"] == 100
    # a second test where everything is wrong or skipped
    d2 = user.post("/screening/sessions", {"role": "python-developer", "level": "medium", "count": 10}).json()
    _finish(user, d2, db, lambda q: None)
    r2 = user.post(f"/screening/sessions/{d2['id']}/submit").json()
    assert r2["session"]["score"] == 0 and r2["next_step"]["next_level"] == "easy" and r2["next_step"]["weak_categories"]
    assert all(i["chosen"] is None and not i["correct"] for i in r2["review"])
    assert [s["score"] for s in user.get("/screening/sessions").json()] == [0, 100]


def test_answers_validate_lock_after_submit_and_stay_private(bank, user, db, make_api):
    d = user.post("/screening/sessions", {"role": "python-developer", "count": 5}).json()
    q = d["questions"][0]["slug"]
    assert user.put(f"/screening/sessions/{d['id']}/answers", {"question": q, "choice": 9}).status_code == 422
    assert user.put(f"/screening/sessions/{d['id']}/answers", {"question": "not-in-test", "choice": 0}).status_code == 404
    assert user.put(f"/screening/sessions/{d['id']}/answers", {"question": q, "choice": 1}).json()["answered"] == 1
    assert user.put(f"/screening/sessions/{d['id']}/answers", {"question": q, "choice": None}).json()["answered"] == 0  # clearing an answer
    assert user.get(f"/screening/sessions/{d['id']}/review").status_code == 409  # answers stay hidden until submit
    other = make_api()
    other.signup("other@example.com")
    assert other.get(f"/screening/sessions/{d['id']}").status_code == 404
    user.post(f"/screening/sessions/{d['id']}/submit")
    assert user.put(f"/screening/sessions/{d['id']}/answers", {"question": q, "choice": 0}).status_code == 409


def test_an_expired_test_is_submitted_automatically_with_the_answers_saved_so_far(bank, user, db):
    d = user.post("/screening/sessions", {"role": "python-developer", "level": "easy", "count": 5}).json()
    qmap = _finish(user, d, db, lambda q: q.answer_index)
    row = db.get(ScreeningSession, d["id"]) if False else db.query(ScreeningSession).one()
    row.deadline_at = utcnow() - timedelta(seconds=1)
    db.commit()
    got = user.get(f"/screening/sessions/{d['id']}").json()
    assert got["status"] == "submitted"
    res = user.get(f"/screening/sessions/{d['id']}/review").json()
    assert res["auto_submitted"] is True and res["session"]["score"] == 100 and len(qmap) == 5


def test_screening_scores_reach_the_progress_dashboard(bank, user, db):
    d = user.post("/screening/sessions", {"role": "python-developer", "level": "easy", "count": 6}).json()
    _finish(user, d, db, lambda q: q.answer_index)
    user.post(f"/screening/sessions/{d['id']}/submit")
    dash = user.get("/reports/dashboard").json()
    assert dash["summary"]["screening_tests"] == 1 and dash["summary"]["average_screening_score"] == 100
    assert dash["screening"][0]["score"] == 100 and dash["screening_categories"]
