from runner.contract import CaseResult, RunnerRequest, RunnerResponse


class MockBackend:
    """DEVELOPMENT MOCK. It does NOT execute code and never reports a pass. Every test comes back `not_run`.
    Use it to build and demonstrate the product flow while no isolated backend is approved."""

    name = "mock"
    version = "1"
    executes_code = False

    def run(self, req: RunnerRequest) -> RunnerResponse:
        return RunnerResponse(
            request_id=req.request_id, backend=self.name, backend_version=self.version, executed=False, compile_error=None,
            tests=[CaseResult(id=t.id, status="not_run") for t in req.tests], total_runtime_ms=None,
        )
