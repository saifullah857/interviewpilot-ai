from typing import Protocol

from runner.contract import RunnerRequest, RunnerResponse


class Backend(Protocol):
    name: str
    version: str
    executes_code: bool

    def run(self, req: RunnerRequest) -> RunnerResponse: ...
