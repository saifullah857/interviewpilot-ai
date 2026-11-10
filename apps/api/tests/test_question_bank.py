import pytest

from app.models.question import BankQuestion
from app.questions import service
from app.questions.schemas import QuestionSpec

GOOD = {
    "slug": "arbisoft-tech-99", "kind": "technical", "category": "python", "difficulty": "easy", "roles": ["python-developer"], "companies": ["arbisoft"],
    "prompt": "Explain what a Python list comprehension is and when you would use one.", "ideal_answer": "A list comprehension builds a list from an iterable in one expression, which is shorter and usually faster than a loop with append.",
    "key_points": ["One-expression list building", "Often faster than append loops"], "follow_ups": [],
}


@pytest.fixture
def bank(db):
    return service.import_bank(db)


@pytest.fixture
def user(make_api):
    u = make_api()
    u.signup("learner@example.com")
    return u


def test_every_file_validates_and_each_company_has_25_distinct_technical_questions(bank, db):
    specs = service.load_dir()
    assert len(specs) == 525 + 105  # technical and scenario questions, plus the screening MCQ and output questions
    by = {}
    for s in specs:
        if s.kind in ("technical", "scenario"):
            by.setdefault(s.companies[0], []).append(s)
    from app.coding import focus

    assert set(by) == {c["slug"] for c in focus.company_profiles()}  # all 21 software houses have their own 25
    for company, items in by.items():
        assert len(items) == 25, company
        assert len({i.prompt for i in items}) == 25
        assert {i.difficulty for i in items} == {"easy", "medium", "hard"}
        assert all(i.source_label == "company_focused_practice" for i in items)  # nothing is claimed to be a real company question


def test_import_is_idempotent(db, bank):
    again = service.import_bank(db)
    assert again["created"] == 0 and again["updated"] == 630


def test_rules_reject_bad_questions():
    for bad in (
        {**GOOD, "key_points": ["only one"]},
        {**GOOD, "source_label": "reported"},  # needs a source note
        {**GOOD, "kind": "mcq"},  # needs options
        {**GOOD, "slug": "Bad Slug"},
        {**GOOD, "unknown_field": 1},
    ):
        with pytest.raises(Exception):  # noqa: B017
            QuestionSpec.model_validate(bad)
    ok = QuestionSpec.model_validate({**GOOD, "source_label": "reported", "source_note": "Shared by a candidate in a public forum, unverified."})
    assert ok.source_label == "reported"
    mcq = QuestionSpec.model_validate({**GOOD, "kind": "mcq", "ideal_answer": "", "key_points": [], "options": ["a", "b", "c"], "answer_index": 1, "explanation": "Because b is right."})
    assert mcq.answer_index == 1
    with pytest.raises(Exception):  # noqa: B017
        QuestionSpec.model_validate({**GOOD, "kind": "mcq", "options": ["a", "a", "c"], "answer_index": 1, "explanation": "Because b is right.", "ideal_answer": "", "key_points": []})


def test_learners_filter_by_company_and_role_and_never_see_answers_in_the_list(bank, user):
    r = user.get("/questions", params={"company": "xeven-solutions", "role": "junior-ai-engineer"}).json()
    assert r["total"] >= 20 and all("xeven-solutions" in q["companies"] and "junior-ai-engineer" in q["roles"] for q in r["items"])
    assert all("ideal_answer" not in q and "answer_index" not in q for q in r["items"])
    assert all(q["source_label"] == "company_focused_practice" and "not a real interview question" in q["source_title"] for q in r["items"])
    rag = user.get("/questions", params={"company": "xeven-solutions", "q": "rag"}).json()
    assert rag["total"] >= 3
    hard = user.get("/questions", params={"company": "arbisoft", "difficulty": "hard"}).json()
    assert hard["total"] >= 3 and all(q["difficulty"] == "hard" for q in hard["items"])
    # the AI company is not shown plain frontend or unrelated questions
    assert user.get("/questions", params={"company": "xeven-solutions", "role": "frontend-developer", "kind": "technical"}).json()["total"] == 0


def test_reveal_and_stats(bank, user):
    slug = user.get("/questions", params={"company": "arbisoft"}).json()["items"][0]["slug"]
    rev = user.post(f"/questions/{slug}/reveal").json()
    assert rev["ideal_answer"] and len(rev["key_points"]) >= 2
    st = user.get("/questions/stats").json()
    assert st["total"] == 630 and len(st["companies"]) == 21
    assert all(c["kind"].get("technical", 0) + c["kind"].get("scenario", 0) == 25 for c in st["companies"]) and st["source"] == {"company_focused_practice": st["total"]}
    assert user.get("/questions/no-such-question").status_code == 404


def test_admin_endpoints_are_admin_only_and_enforce_the_same_rules(bank, db, user, make_api):
    assert user.post("/admin/questions", GOOD).status_code in (401, 403)
    admin = make_api()
    admin.signup("boss@example.com")
    from sqlalchemy import select

    from app.models.user import User

    db.scalars(select(User).where(User.email == "boss@example.com")).one().role = "admin"
    db.commit()
    assert admin.post("/admin/questions", GOOD).status_code == 201
    assert admin.post("/admin/questions", GOOD).status_code == 409  # slug taken
    assert admin.post("/admin/questions", {**GOOD, "slug": "arbisoft-tech-98"}).status_code == 409  # same prompt for the same company
    assert admin.post("/admin/questions", {**GOOD, "slug": "arbisoft-tech-97", "prompt": "Explain what a Python dictionary comprehension is and when it helps.", "companies": ["not-a-company"]}).status_code == 422
    assert admin.patch("/admin/questions/arbisoft-tech-99", {"enabled": False}).status_code == 200
    assert user.get("/questions/arbisoft-tech-99").status_code == 404  # disabled questions disappear for learners
    assert admin.get("/admin/questions", params={"q": "comprehension"}).json()["total"] >= 1  # but the admin still sees them
    assert admin.patch("/admin/questions/arbisoft-tech-99", {"source_label": "verified"}).status_code == 422  # needs a source note
    assert admin.patch("/admin/questions/arbisoft-tech-99", {"source_label": "verified", "source_note": "Published by the company on its careers page."}).status_code == 200
    assert admin.delete("/admin/questions/arbisoft-tech-99").status_code == 204
    assert db.scalars(select(BankQuestion).where(BankQuestion.slug == "arbisoft-tech-99")).first() is None
