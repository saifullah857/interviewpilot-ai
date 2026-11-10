"""Vendored copy of services/sandbox-runner/runner/contract.py. A test fails if the two drift apart. Do not edit one without the other."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

CONTRACT_VERSION = "1"
IDENT = r"^[A-Za-z_][A-Za-z0-9_]{0,63}$"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CaseSpec(_Strict):
    id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,40}$")
    args: list[Any]
    expected: Any
    tolerance: float | None = Field(default=None, ge=0, le=1)


class Limits(_Strict):
    per_test_ms: int = Field(default=2000, ge=50, le=10_000)
    total_wall_s: int = Field(default=20, ge=1, le=60)
    memory_mb: int = Field(default=256, ge=32, le=1024)
    output_kb: int = Field(default=16, ge=1, le=64)


class RunnerRequest(_Strict):
    request_id: str = Field(pattern=r"^[A-Za-z0-9_-]{8,64}$")
    language: Literal["python"]
    entry_point: str = Field(pattern=IDENT)
    code: str = Field(min_length=1, max_length=20_000)
    tests: list[CaseSpec] = Field(min_length=1, max_length=60)
    limits: Limits = Field(default_factory=Limits)


class CaseResult(_Strict):
    id: str
    status: Literal["passed", "failed", "error", "timeout", "not_run"]
    runtime_ms: float | None = Field(default=None, ge=0)
    actual: str | None = Field(default=None, max_length=2000)  # JSON text of the returned value
    error: str | None = Field(default=None, max_length=500)
    stdout: str | None = Field(default=None, max_length=2000)


class RunnerResponse(_Strict):
    request_id: str
    backend: str = Field(max_length=40)
    backend_version: str = Field(max_length=40)
    executed: bool
    compile_error: str | None = Field(default=None, max_length=500)
    tests: list[CaseResult]
    total_runtime_ms: float | None = Field(default=None, ge=0)
