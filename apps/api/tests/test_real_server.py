"""Tests over a REAL socket (uvicorn in a thread). The in-process test client never exercises the HTTP framing, so a bug such as a body on
a 204 response, which a real server rejects by resetting the connection, was invisible to every other test."""

import re
import threading
import time
from pathlib import Path

import httpx
import pytest

PASSWORD = "correct horse battery"
APP_DIR = Path(__file__).resolve().parents[1] / "app"


@pytest.fixture
def live(app):
    import uvicorn

    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=0, log_level="warning", lifespan="off"))
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    for _ in range(200):
        if server.started:
            break
        time.sleep(0.05)
    assert server.started, "the test server did not start"
    port = server.servers[0].sockets[0].getsockname()[1]
    yield f"http://127.0.0.1:{port}/api/v1"
    server.should_exit = True
    t.join(5)


def client(base):
    c = httpx.Client(base_url=base, timeout=20)
    token = c.get("/auth/csrf").json()["csrf_token"]
    return c, {"X-CSRF-Token": token}


def test_204_responses_are_valid_http_and_the_connection_survives(live):
    """Each 204 below is followed by another request on the SAME keep-alive connection. A body on a 204 makes the server reset it."""
    c, h = client(live)
    assert c.post("/auth/signup", json={"email": "live@example.com", "password": PASSWORD, "display_name": "Live"}, headers=h).status_code == 201
    r = c.post("/me/password", json={"current_password": PASSWORD, "new_password": "another passphrase 77"}, headers=h)
    assert r.status_code == 204 and r.content == b""
    assert c.get("/me").status_code == 200  # same connection, still alive
    assert c.post("/auth/logout", headers=h).status_code in (200, 204)
    assert c.get("/auth/csrf").status_code == 200
    c2, h2 = client(live)
    assert c2.post("/auth/login", json={"email": "live@example.com", "password": "another passphrase 77"}, headers=h2).status_code == 200
    gone = c2.request("DELETE", "/me", json={"password": "another passphrase 77"}, headers=h2)
    assert gone.status_code == 204 and gone.content == b""
    assert c2.get("/auth/csrf").status_code == 200  # the connection is still usable after the account is deleted


def test_no_route_builds_a_204_with_a_json_body():
    """A 204 must have no body at all. `JSONResponse(None, 204)` sends the text `null`, which is a protocol error on a real server."""
    offenders = [str(p.relative_to(APP_DIR)) for p in APP_DIR.rglob("*.py") if re.search(r"JSONResponse\(\s*None", p.read_text())]
    assert offenders == [], offenders
