"""Makes apps/api/.env ready for the local code runner. Safe to run many times; it never prints secrets and keeps all your other settings.
Sets RUNNER_MODE=local: submitted code is run by the built-in runner inside the API, so no separate runner window is needed."""
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV = ROOT / "apps" / "api" / ".env"
EXAMPLE = ROOT / "apps" / "api" / ".env.example"


def main() -> int:
    if not ENV.exists():
        shutil.copyfile(EXAMPLE, ENV)
        print("Created apps\\api\\.env from .env.example. Add your GROQ_API_KEY and TAVILY_API_KEY there, then run START.bat again.")
    lines = ENV.read_text(encoding="utf-8").splitlines()
    values = {m.group(1): m.group(2).strip().strip('"\'') for l in lines if (m := re.match(r"^([A-Z_]+)=(.*)$", l))}
    want = {"RUNNER_MODE": "local"}
    seen = set()
    out = []
    for l in lines:
        m = re.match(r"^([A-Z_]+)=", l)
        if m and m.group(1) in want:
            out.append(f"{m.group(1)}={want[m.group(1)]}")
            seen.add(m.group(1))
        else:
            out.append(l)
    for k, v in want.items():
        if k not in seen:
            out.append(f"{k}={v}")
    ENV.write_text("\n".join(out) + "\n", encoding="utf-8")
    for key in ("GROQ_API_KEY", "TAVILY_API_KEY"):
        if not values.get(key):
            print(f"NOTE: {key} is empty in apps\\api\\.env. " + ("AI features will use the built-in question bank only." if key == "GROQ_API_KEY" else "Company research will be unavailable."))
    print("Runner settings are ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
