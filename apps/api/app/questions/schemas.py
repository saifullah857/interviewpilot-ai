import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Kind = Literal["technical", "scenario", "mcq", "output"]
Difficulty = Literal["easy", "medium", "hard"]
Source = Literal["verified", "reported", "company_focused_practice"]

SOURCE_TITLES = {
    "verified": "Verified: supported by an identifiable source",
    "reported": "Reported: shared by a candidate or community, not independently verified",
    "company_focused_practice": "Company-focused practice: written for this company's technology focus, not a real interview question",
}
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{2,78}$")


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


class QuestionSpec(BaseModel):
    """The one shape a question has everywhere: import files, admin forms and the database."""

    model_config = ConfigDict(extra="forbid")
    slug: str
    kind: Kind
    category: str = Field(min_length=2, max_length=40)
    difficulty: Difficulty
    roles: list[str] = Field(min_length=1, max_length=15)
    companies: list[str] = Field(min_length=1, max_length=30)
    topics: list[str] = Field(default_factory=list, max_length=8)
    prompt: str = Field(min_length=10, max_length=2000)
    ideal_answer: str = Field(default="", max_length=4000)
    key_points: list[str] = Field(default_factory=list, max_length=10)
    follow_ups: list[str] = Field(default_factory=list, max_length=5)
    options: list[str] = Field(default_factory=list, max_length=6)
    answer_index: int | None = None
    explanation: str = Field(default="", max_length=2000)
    source_label: Source = "company_focused_practice"
    source_note: str = Field(default="", max_length=300)
    enabled: bool = True

    @field_validator("slug")
    @classmethod
    def _slug(cls, v: str) -> str:
        if not SLUG.match(v):
            raise ValueError("slug must be lowercase letters, digits and dashes")
        return v

    @model_validator(mode="after")
    def _rules(self) -> "QuestionSpec":
        if self.kind in ("technical", "scenario"):
            if len(self.prompt) < 25:
                raise ValueError("a technical question needs a prompt of at least 25 characters")
            if len(self.ideal_answer) < 40 or len(self.key_points) < 2:
                raise ValueError("a technical question needs an ideal answer and at least 2 key points")
            if self.options or self.answer_index is not None:
                raise ValueError("options belong to mcq and output questions only")
        else:
            if len(self.options) < 3 or self.answer_index is None or not 0 <= self.answer_index < len(self.options):
                raise ValueError("an mcq or output question needs 3+ options and a valid answer_index")
            if len({o.strip() for o in self.options}) != len(self.options) or any(not o.strip() for o in self.options):  # exact comparison: (3, 9) and [3, 9] are different answers
                raise ValueError("options must differ")
            if len(self.explanation) < 15:
                raise ValueError("an mcq or output question needs an explanation")
        if self.source_label != "company_focused_practice" and len(self.source_note) < 10:
            raise ValueError("verified and reported questions need a source_note that says where the claim comes from")
        return self


class QuestionOut(BaseModel):
    """What a learner sees before answering: no ideal answer, no correct option."""

    slug: str
    kind: str
    category: str
    difficulty: str
    roles: list[str]
    companies: list[str]
    topics: list[str]
    prompt: str
    options: list[str]
    source_label: str
    source_title: str


class RevealOut(BaseModel):
    slug: str
    ideal_answer: str
    key_points: list[str]
    follow_ups: list[str]
    answer_index: int | None
    explanation: str
    source_label: str
    source_note: str


class AdminQuestionOut(QuestionSpec):
    id: str


class QuestionPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Kind | None = None
    category: str | None = Field(default=None, min_length=2, max_length=40)
    difficulty: Difficulty | None = None
    roles: list[str] | None = None
    companies: list[str] | None = None
    topics: list[str] | None = None
    prompt: str | None = Field(default=None, min_length=10, max_length=2000)
    ideal_answer: str | None = None
    key_points: list[str] | None = None
    follow_ups: list[str] | None = None
    options: list[str] | None = None
    answer_index: int | None = None
    explanation: str | None = None
    source_label: Source | None = None
    source_note: str | None = None
    enabled: bool | None = None
