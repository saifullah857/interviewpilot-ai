import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.assessments.validate import _MARKUP, _URL


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProblemSummary(BaseModel):
    slug: str
    title: str
    difficulty: str
    minutes: int
    topics: list[str]
    roles: list[str]
    tags: list[str] = []
    ds: list[str] = []  # list, tuple, dict, set, loop, condition: what the problem makes you combine


class PublicTest(BaseModel):
    __test__ = False
    id: str
    args: list[Any]
    expected: Any


class PublicExample(BaseModel):
    args: list[Any]
    output: Any
    explanation: str


class ProblemPublic(ProblemSummary):
    """Everything a candidate may see before finishing. No hidden tests, reference solution, approach or complexity."""

    statement: str
    constraints: list[str]
    signature: str
    starter_code: str
    examples: list[PublicExample]
    visible_tests: list[PublicTest]
    hidden_count: int
    per_test_ms: int
    label: str


class CreateSessionIn(_Strict):
    problem_slugs: list[str] | None = Field(default=None, min_length=1, max_length=3)
    assessment_id: uuid.UUID | None = None
    role: str | None = Field(default=None, max_length=80)
    count: int = Field(default=2, ge=1, le=3)
    company: str | None = Field(default=None, max_length=80)  # software house slug: shapes which problems you get (role mode only)
    resume_id: uuid.UUID | None = None  # resume whose skills and languages shape the problems (role mode only)
    company_set: bool = False  # take the problems from the company's 25-problem set, skipping ones already solved (needs role and company)

    @model_validator(mode="after")
    def _one_way(self) -> "CreateSessionIn":
        chosen = [x for x in (self.problem_slugs, self.assessment_id, self.role) if x is not None]
        if len(chosen) != 1:
            raise ValueError("Give exactly one of problem_slugs, assessment_id or role.")
        if self.problem_slugs and len(set(self.problem_slugs)) != len(self.problem_slugs):
            raise ValueError("problem_slugs must be distinct.")
        if self.company_set and not (self.role and self.company):
            raise ValueError("company_set needs a role and a company.")
        return self


class CodeIn(_Strict):
    problem: str = Field(min_length=1, max_length=80)
    code: str = Field(max_length=60_000)
    language: Literal["python"] = "python"


class DraftIn(_Strict):
    code: str = Field(max_length=60_000)


class ResultOut(BaseModel):
    id: str
    hidden: bool
    label: str
    status: Literal["passed", "failed", "error", "timeout", "not_run"]
    runtime_ms: float | None = None
    args: list[Any] | None = None
    expected: Any | None = None
    actual: str | None = None
    error: str | None = None
    stdout: str | None = None


class CodeFeedback(_Strict):
    complexity: str = Field(min_length=3, max_length=300)
    strengths: list[str] = Field(default_factory=list, max_length=4)
    improvements: list[str] = Field(default_factory=list, max_length=5)
    readability: str = Field(default="", max_length=300)

    @field_validator("complexity", "readability", "strengths", "improvements")
    @classmethod
    def _plain_text(cls, v):
        items = v if isinstance(v, list) else [v]
        if any(len(x) > 300 or _URL.search(x) or _MARKUP.search(x) for x in items):
            raise ValueError("Feedback must be plain text without links or markup.")
        return v


class SubmissionOut(BaseModel):
    id: uuid.UUID
    kind: str
    problem: str
    status: str
    executed: bool
    compile_error: str | None
    passed_count: int | None
    total_count: int
    runtime_ms: float | None
    runner_backend: str
    message: str | None
    results: list[ResultOut]
    created_at: datetime
    feedback: dict | None = None


class Progress(BaseModel):
    problem: str
    runs: int
    submits: int
    last_submit: SubmissionOut | None


class SessionOut(BaseModel):
    id: uuid.UUID
    status: str
    assessment_id: uuid.UUID | None
    problem_slugs: list[str]
    problems: list[ProblemPublic] | None = None
    drafts: dict[str, str]
    progress: list[Progress]
    started_at: datetime
    deadline_at: datetime
    submitted_at: datetime | None
    auto_submitted: bool
    server_now: datetime
    runs_left: int
    submits_left: int
    company: dict | None = None
    language: str = "python"
    plan: dict = {}


class SessionSummary(BaseModel):
    id: uuid.UUID
    status: str
    problem_slugs: list[str]
    started_at: datetime
    deadline_at: datetime
    submitted_at: datetime | None
    tests_passed: int | None
    tests_total: int
    executed: bool
    company: dict | None = None
    score: int | None = None  # percentage of tests passed, None when nothing was executed
    solved: int = 0
    problems: int = 0


class ReviewProblem(BaseModel):
    problem: ProblemPublic
    approach: str
    complexity: dict[str, str]
    reference_solution: str
    final_code: str
    runs: int
    submits: int
    submission: SubmissionOut | None
    passed_count: int | None
    total_count: int
    solved: bool


class ReviewOut(BaseModel):
    session: SessionOut
    problems: list[ReviewProblem]
    summary: dict


class RunnerStatus(BaseModel):
    mode: str
    executes_code: bool
    reachable: bool
    backend: str
    message: str
