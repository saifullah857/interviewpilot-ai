# SANDBOX_DESIGN.md — running candidates' code (ADR-006)

**Status (Phase 12, 2026-10-30): a real sandboxed backend now exists** (`RUNNER_BACKEND=bwrap`, bubblewrap, no Docker; decided by you on 2026-10-30 as ADR-006 option B). It runs on Linux and, on Windows, inside WSL2. It was built and tested only on a Linux machine; **you have not run it on Windows yet**. On plain Windows without WSL2 the coding feature still uses the mock and shows "Not run". Sections 1 to 6 below are the original design and the history; section 7 is what was built.

## 1. What can go wrong
Candidates' code is untrusted. Left unsandboxed it can: loop forever or eat memory (denial of service), read files or environment variables (steal API keys, the database password, other users' resumes), open network connections (call internal services, exfiltrate data, attack other machines), write files or spawn processes (persist, fork-bomb), print gigabytes of output, or crash its host. The rule from the brief: **never execute untrusted code inside the FastAPI process**, and use strict CPU, memory, time, filesystem, network and process limits.

## 2. What exists now
| Piece | Where | State |
|---|---|---|
| API-side pipeline (problems, sessions, drafts, run, submit, hidden-test redaction, review, AI commentary) | `apps/api/app/coding/` | Built and tested. The API never executes code (a test scans `app/` for `exec`, `eval`, `compile`, `os.system`, `subprocess`, ... and fails if any appear, except our fixed document-parsing worker) |
| Contract (request/response, test cases, limits) | `services/sandbox-runner/runner/contract.py` (copy in `apps/api/app/coding/runner_contract.py`; a test fails if they drift) | Built |
| Runner service: HMAC-signed requests, 60-second clock window, replay refusal, 1 MB size cap, strict schema | `services/sandbox-runner/runner/app.py` | Built and tested; backend = mock only |
| Mock backend | `runner/backends/mock.py` | Executes nothing; every test `not_run` |
| In-sandbox harness (what a real backend runs inside its sandbox) | `runner/harness.py` | Built; tested with trusted fixtures only; **not a sandbox itself** |
| Problem bank with hidden tests | `data/coding/problems.json` (built by `scripts/build_coding_problems.py`) | 10 problems; each reference solution passes all its tests and 20 deliberately wrong solutions are caught |
| Hostile-program conformance suite | `apps/api/tests/runner/test_conformance_hostile.py` | Written; **skipped** until a real backend exists |

The API validates every runner reply against what it asked (same request id, same test ids in the same order, a non-executing runner may only say `not_run`) and discards anything inconsistent.

## 3. Options (decision needed)
- **A. Docker Desktop (WSL2 backend), for the runner only. Recommended.** The runner starts one short-lived container per run.
- **B. WSL2 Linux with a native sandbox (for example nsjail or bubblewrap), no Docker.** Fewer moving parts at run time but harder to set up and tune; not verified on your machine.
- **C. A hosted judge service.** Quick, but candidates' code (and our hidden tests) go to a third party; terms and cost not checked.
- **D. Keep the mock.** The whole flow stays demonstrable, but code is never tested and Phase 7 is never "complete".

## 4. What option A would do (design, not built)
Per run, the runner would execute roughly: `docker run --rm --network none --read-only --tmpfs /work:rw,noexec,size=16m --memory 256m --memory-swap 256m --cpus 1 --pids-limit 64 --cap-drop ALL --security-opt no-new-privileges --user 65534:65534 -v <harness>:/harness:ro <pinned python image> python /harness/harness.py /work/req.json /work/res.json`, with the request written to a temporary directory, a wall-clock kill after `total_wall_s` (container force-removed even if the harness hangs), output and result size caps, and a missing or oversized result file treated as an error. The image would be a minimal pinned Python image with no extra packages. The runner process itself would run as a normal user, listen on localhost only, accept only signed requests, limit concurrency, and never pass the API's environment to a container.
Honest caveats: access to the Docker daemon is powerful (equivalent to administrator rights on the Docker VM), so the runner is a high-value target and must stay local; on Windows the WSL2 VM is the real boundary; containers are not as strong as a micro-VM, so this is acceptable for a local MVP and **not** for serving the public internet. Docker was not available in the environment where this was written, so none of option A has been run. Docker's licence terms for your use are unchecked.

## 5. Acceptance criteria for calling Phase 7 complete
1. A real backend is approved and built behind the existing contract (`RUNNER_BACKEND=<name>`; the API only needs `RUNNER_MODE=http`).
2. `pytest apps/api/tests/runner/test_conformance_hostile.py` passes against it (set `RUNNER_CONFORMANCE_URL` and `RUNNER_SHARED_SECRET`): infinite loop, ignoring the alarm signal, memory bomb, fork bomb attempt, network access, writing outside the work folder, spawning a process, exiting the interpreter, endless output, deep recursion, reading the runner's environment (the secret must not appear), and a correct solution still passing afterwards, with the runner healthy after each.
3. Containers/processes left behind after the suite: none (checked by hand and documented).
4. Per-test timeouts, memory limit and output cap verified under the backend, on the user's machine.
5. Windows setup instructions tested by the user.
6. Problem bank re-validated against the real backend (every reference solution passes, wrong ones fail) with realistic timings.

**Status of these criteria (2026-10-30):** 1 met. 2 met: 12 of 12 passed against the live service started as an unprivileged user. 3 met: no processes or temp folders left, checked by hand and by automated tests. 4 met on Linux; **not yet on your machine**. 5 **not met: only you can do this**. 6 met: all 10 reference solutions pass every visible and hidden test, all 10 starter files fail, all 21 wrong solutions are caught, with timings under half of each problem's limit.

## 6. Until then
The interface says so everywhere: a banner on the coding pages, "Nothing was run" on every Run/Submit, "Not run" and "n/a" instead of scores, and no pass/fail is ever fabricated. Reports (Phase 9) must treat coding correctness as unavailable when `executed` is false.


## 7. What was built: the bubblewrap backend (Phase 12)
**Containment (one fresh sandbox per test):** new user, pid, network, ipc, uts and cgroup namespaces; all capabilities dropped; nested user namespaces disabled; runs as uid 65534; empty environment; a read-only view of `/usr` only (no home, no `/etc`, no project files, none of the runner's own files except the harness); a private 16 MiB `/tmp`. The harness then sets hard limits inside (soft = hard, so code cannot raise them): memory (address space), CPU seconds, file size 1 MiB, 64 open files, **16 processes**, no core files.
**Time:** the harness's alarm handles ordinary overruns, but hostile code can ignore it, so the runner also enforces a wall-clock deadline from outside (3x the per-test limit plus 1 second, never beyond the total limit) and kills the whole sandbox. A killed or hung test is reported as `timeout`, never `not_run` (the API rejects an executing runner that leaves tests unrun).
**Answers stay outside:** the sandbox receives only the code and the test arguments. Expected answers never enter it; the harness reports what the function returned and the trusted runner compares it. A reply is re-validated and clipped, and a reported "passed" is never accepted from inside. Returned values up to 150,000 characters are compared (the largest legitimate answer in the bank is about 69,000).
**Fail closed:** at startup a probe runs inside the sandbox and verifies nine properties (network blocked, host paths hidden, clean environment, read-only `/usr`, unprivileged uid, no capabilities, no nested namespaces, private pid namespace, size-limited `/tmp`). If any fails, or bubblewrap is missing, or Python is not under `/usr`, the service refuses to start. It also **refuses to run as root**, because Linux exempts root-owned processes from the process-count limit that stops fork bombs (found by testing: as root, a fork bomb exhausted this machine's memory).
**Service:** runs happen off the event loop with at most 2 at a time (`RUNNER_MAX_PARALLEL`), so `/health` answers during a run.
**Residual risks (read these):** (1) a Linux kernel vulnerability could escape any namespace sandbox; keep WSL and the kernel updated. (2) No seccomp filter is installed; the process, memory and file limits and the missing network/filesystem carry the load. (3) Total memory of one run is bounded by (processes x per-process limit), up to roughly 16 x (limit + 100 MiB) in the worst case; the default 256 MiB limit means a hostile run can use a lot of RAM for its few seconds. (4) A program can forge the *reported* output of tests whose expected answer it already knows (the visible ones) but cannot learn hidden answers; it can still try guesses by submitting repeatedly (rate-limited). (5) This protects a single-user practice tool. It is not reviewed for running other people's code on a public server.
**Tests:** `apps/api/tests/runner/test_bwrap_backend.py` (68 tests, including the whole bank under real execution) and `test_conformance_hostile.py` (12 hostile programs against the live service). They skip automatically where bubblewrap is unavailable or when run as root.
