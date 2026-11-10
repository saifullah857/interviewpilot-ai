"""Test doubles for the code runner. NONE of them executes code: they answer from markers in the submitted text."""

from app.coding.runner_contract import CaseResult, RunnerRequest, RunnerResponse


class ScriptedRunner:
    mode = "scripted"

    def __init__(self):
        self.calls: list[RunnerRequest] = []

    def status(self):
        return {"mode": "scripted", "executes_code": True, "reachable": True, "backend": "scripted", "message": "test double"}

    def run(self, req: RunnerRequest) -> RunnerResponse:
        self.calls.append(req)
        code = req.code
        if "COMPILE" in code:
            tests = [CaseResult(id=t.id, status="error", error="SyntaxError: bad (line 1)") for t in req.tests]
            return RunnerResponse(
                request_id=req.request_id,
                backend="scripted",
                backend_version="1",
                executed=True,
                compile_error="SyntaxError: bad (line 1)",
                tests=tests,
                total_runtime_ms=1,
            )
        out = []
        for t in req.tests:
            hidden = t.id.startswith("h")
            if "PASS_ALL" in code:
                r = CaseResult(id=t.id, status="passed", runtime_ms=1.5, actual="1")
            elif "FAIL_HIDDEN" in code:
                r = CaseResult(id=t.id, status="failed" if hidden else "passed", runtime_ms=2.0, actual="999 secret-actual-value" if hidden else "1")
            elif "ERROR_HIDDEN" in code:
                r = CaseResult(
                    id=t.id,
                    status="error" if hidden else "passed",
                    runtime_ms=2.0,
                    error="ValueError: secret hidden detail" if hidden else None,
                    stdout="leaky stdout" if hidden else None,
                )
            elif "TIMEOUT" in code:
                r = CaseResult(id=t.id, status="timeout", runtime_ms=2000.0, error="Exceeded 2000 ms")
            else:
                r = CaseResult(id=t.id, status="failed", runtime_ms=1.0, actual="0")
            out.append(r)
        return RunnerResponse(
            request_id=req.request_id,
            backend="scripted",
            backend_version="1",
            executed=True,
            compile_error=None,
            tests=out,
            total_runtime_ms=sum(x.runtime_ms or 0 for x in out),
        )
