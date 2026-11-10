import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.coding import CodingProblem

DEFAULT_BANK = Path(__file__).resolve().parents[4] / "data" / "coding" / "problems.json"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TestSpec(_Strict):
    __test__ = False  # not a pytest test class
    id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,40}$")
    args: list[Any]
    expected: Any
    hidden: bool
    tolerance: float | None = Field(default=None, ge=0, le=1)


class Example(_Strict):
    args: list[Any]
    output: Any
    explanation: str = Field(min_length=3, max_length=300)


class ProblemSpec(_Strict):
    slug: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$", max_length=80)
    title: str = Field(min_length=3, max_length=200)
    difficulty: str = Field(pattern="^(easy|medium|hard)$")
    minutes: int = Field(ge=10, le=60)
    topics: list[str] = Field(min_length=1, max_length=8)
    roles: list[str] = Field(min_length=1, max_length=8)
    tags: list[str] = Field(default_factory=list, max_length=10)  # focus tags: match a software house profile and resume skills
    ds: list[str] = Field(default_factory=list, max_length=8)  # Python structures the problem combines (list, tuple, dict, set, loop, condition)
    statement: str = Field(min_length=80, max_length=4000)
    constraints: list[str] = Field(min_length=1, max_length=10)
    entry_point: str = Field(pattern=r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")
    signature: str = Field(max_length=200)
    starter_code: str = Field(max_length=2000)
    examples: list[Example] = Field(min_length=1, max_length=4)
    visible_tests: list[TestSpec] = Field(min_length=3, max_length=6)
    hidden_tests: list[TestSpec] = Field(min_length=6, max_length=30)
    per_test_ms: int = Field(ge=100, le=10_000)
    complexity: dict[str, str]
    approach: str = Field(min_length=20, max_length=2000)
    reference_solution: str = Field(min_length=20, max_length=5000)

    @field_validator("visible_tests")
    @classmethod
    def _visible(cls, v: list[TestSpec]) -> list[TestSpec]:
        if any(t.hidden for t in v):
            raise ValueError("visible tests must have hidden=false")
        return v

    @field_validator("hidden_tests")
    @classmethod
    def _hidden(cls, v: list[TestSpec]) -> list[TestSpec]:
        if not all(t.hidden for t in v):
            raise ValueError("hidden tests must have hidden=true")
        return v

    @model_validator(mode="after")
    def _checks(self) -> "ProblemSpec":
        ids = [t.id for t in self.visible_tests + self.hidden_tests]
        if len(ids) != len(set(ids)):
            raise ValueError("test ids must be unique")
        if self.signature not in self.starter_code or self.entry_point not in self.signature:
            raise ValueError("starter code must contain the signature of the entry point")
        return self


class Bank(_Strict):
    meta: dict = Field(alias="_meta")
    problems: list[ProblemSpec]

    @model_validator(mode="after")
    def _unique(self) -> "Bank":
        slugs = [p.slug for p in self.problems]
        if len(slugs) != len(set(slugs)):
            raise ValueError("duplicate problem slugs")
        return self


def load_bank(path: Path = DEFAULT_BANK) -> Bank:
    return Bank.model_validate(json.loads(path.read_text(encoding="utf-8")))


def import_bank(db: Session, path: Path = DEFAULT_BANK) -> dict[str, int]:
    bank = load_bank(path)
    out = {"created": 0, "updated": 0}
    for p in bank.problems:
        data = p.model_dump(mode="json")
        row = db.scalars(select(CodingProblem).where(CodingProblem.slug == p.slug)).first()
        if row is None:
            db.add(CodingProblem(**data, label="ai_generated_practice", active=True))
            out["created"] += 1
        else:
            for k, v in data.items():
                setattr(row, k, v)
            row.active = True
            out["updated"] += 1
    db.commit()
    return out
