import json
from collections import Counter
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.coding import focus
from app.core.errors import AppError, not_found
from app.models.question import BankQuestion
from app.questions.schemas import SOURCE_TITLES, AdminQuestionOut, QuestionOut, QuestionPatch, QuestionSpec, RevealOut, norm
from app.resumes import roles

ROOT = Path(__file__).resolve().parents[4]
BANK_DIR = ROOT / "data" / "questions"


def valid_companies() -> set[str]:
    return {c["slug"] for c in focus.company_profiles()}


def valid_roles() -> set[str]:
    return {r["slug"] for r in roles.list_roles()}


def check_refs(spec: QuestionSpec) -> None:
    bad_c = [c for c in spec.companies if c not in valid_companies()]
    bad_r = [r for r in spec.roles if r not in valid_roles()]
    if bad_c or bad_r:
        raise AppError(422, "unknown_reference", f"Unknown company {bad_c} or role {bad_r}.")


def load_dir(directory: Path = BANK_DIR) -> list[QuestionSpec]:
    """Reads and validates every data/questions/*.json file. Raises on the first bad question, naming it."""
    specs: list[QuestionSpec] = []
    for f in sorted([*directory.glob("*.json"), *directory.glob("screening/*.json")]):
        for i, raw in enumerate(json.loads(f.read_text(encoding="utf-8"))["questions"]):
            try:
                specs.append(QuestionSpec.model_validate(raw))
            except Exception as e:  # noqa: BLE001
                raise ValueError(f"{f.name} question #{i + 1} ({raw.get('slug')}): {e}") from e
    slugs = [s.slug for s in specs]
    if len(slugs) != len(set(slugs)):
        raise ValueError("duplicate slugs in the question bank")
    seen: dict[str, str] = {}
    for s in specs:
        for c in s.companies:
            key = (c, norm(s.prompt))
            if key in seen:
                raise ValueError(f"duplicate question for {c}: {s.slug} repeats {seen[key]}")
            seen[key] = s.slug
    for s in specs:
        check_refs(s)
    return specs


def import_bank(db: Session, directory: Path = BANK_DIR) -> dict[str, int]:
    out = {"created": 0, "updated": 0}
    for s in load_dir(directory):
        data = s.model_dump()
        row = db.scalars(select(BankQuestion).where(BankQuestion.slug == s.slug)).first()
        if row is None:
            db.add(BankQuestion(**data))
            out["created"] += 1
        else:
            for k, v in data.items():
                setattr(row, k, v)
            out["updated"] += 1
    db.commit()
    return out


def public(q: BankQuestion) -> QuestionOut:
    return QuestionOut(slug=q.slug, kind=q.kind, category=q.category, difficulty=q.difficulty, roles=list(q.roles), companies=list(q.companies), topics=list(q.topics), prompt=q.prompt, options=list(q.options), source_label=q.source_label, source_title=SOURCE_TITLES[q.source_label])


def search(db: Session, company=None, role=None, category=None, difficulty=None, kind=None, source=None, text=None, include_disabled=False, limit=50, offset=0) -> tuple[int, list[BankQuestion]]:
    q = select(BankQuestion).order_by(BankQuestion.slug)
    if not include_disabled:
        q = q.where(BankQuestion.enabled.is_(True))
    for col, val in ((BankQuestion.category, category), (BankQuestion.difficulty, difficulty), (BankQuestion.kind, kind), (BankQuestion.source_label, source)):
        if val:
            q = q.where(col == val)
    rows = db.scalars(q).all()
    if company:
        rows = [r for r in rows if company in r.companies]
    if role:
        rows = [r for r in rows if role in r.roles]
    if text:
        t = text.lower()
        rows = [r for r in rows if t in r.prompt.lower() or any(t in x.lower() for x in r.topics)]
    return len(rows), rows[offset: offset + limit]


def get(db: Session, slug: str, include_disabled: bool = False) -> BankQuestion:
    q = db.scalars(select(BankQuestion).where(BankQuestion.slug == slug)).first()
    if q is None or (not q.enabled and not include_disabled):
        raise not_found("Question")
    return q


def reveal(q: BankQuestion) -> RevealOut:
    return RevealOut(slug=q.slug, ideal_answer=q.ideal_answer, key_points=list(q.key_points), follow_ups=list(q.follow_ups), answer_index=q.answer_index, explanation=q.explanation, source_label=q.source_label, source_note=q.source_note)


def stats(db: Session) -> dict:
    rows = db.scalars(select(BankQuestion).where(BankQuestion.enabled.is_(True))).all()
    names = {c["slug"]: c["name"] for c in focus.company_profiles()}
    per: dict[str, dict] = {}
    for r in rows:
        for c in r.companies:
            d = per.setdefault(c, {"slug": c, "name": names.get(c, c), "total": 0, "kind": Counter(), "difficulty": Counter(), "source": Counter(), "roles": Counter()})
            d["total"] += 1
            d["kind"][r.kind] += 1
            d["difficulty"][r.difficulty] += 1
            d["source"][r.source_label] += 1
            for ro in r.roles:
                d["roles"][ro] += 1
    comp = [{**d, "kind": dict(d["kind"]), "difficulty": dict(d["difficulty"]), "source": dict(d["source"]), "roles": dict(d["roles"])} for d in sorted(per.values(), key=lambda x: x["name"])]
    return {"total": len(rows), "companies": comp, "source": dict(Counter(r.source_label for r in rows)), "categories": dict(Counter(r.category for r in rows)), "source_titles": SOURCE_TITLES}


def create(db: Session, spec: QuestionSpec) -> BankQuestion:
    check_refs(spec)
    if db.scalars(select(BankQuestion).where(BankQuestion.slug == spec.slug)).first():
        raise AppError(409, "slug_taken", "A question with this slug already exists.")
    for r in db.scalars(select(BankQuestion)).all():
        if norm(r.prompt) == norm(spec.prompt) and set(r.companies) & set(spec.companies):
            raise AppError(409, "duplicate_question", f"This repeats {r.slug} for the same company.")
    q = BankQuestion(**spec.model_dump())
    db.add(q)
    db.commit()
    return q


def update(db: Session, slug: str, patch: QuestionPatch) -> BankQuestion:
    q = get(db, slug, include_disabled=True)
    merged = {**AdminQuestionOut.model_validate({**{c: getattr(q, c) for c in QuestionSpec.model_fields}, "id": str(q.id)}).model_dump(exclude={"id"}), **patch.model_dump(exclude_unset=True)}
    try:
        spec = QuestionSpec.model_validate(merged)  # the same rules as on import
    except ValidationError as e:
        raise AppError(422, "invalid_question", "; ".join(x["msg"] for x in e.errors())[:300]) from e
    check_refs(spec)
    for k, v in spec.model_dump().items():
        setattr(q, k, v)
    db.commit()
    return q


def delete(db: Session, slug: str) -> None:
    db.delete(get(db, slug, include_disabled=True))
    db.commit()
