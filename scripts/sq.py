"""Authoring helpers for screening (MCQ and output) questions. Output answers are NOT typed by hand: the code is executed here
(Python, Node or SQLite) and the real result becomes the correct option, so an answer can never be wrong."""
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "questions" / "screening"
ALLR = ["python-developer", "backend-developer", "full-stack-developer", "frontend-developer", "mobile-app-developer", "ai-ml-engineer-intern", "junior-ai-engineer", "data-scientist"]
SEED = json.loads((Path(__file__).resolve().parent.parent / "data" / "company_seed" / "lahore_candidates.json").read_text(encoding="utf-8"))["companies"]
ALLC = [c["slug"] for c in SEED]
GROUPS = {
    "all": (ALLC, ALLR),
    "ai": (["xeven-solutions", "folio3", "conrad-labs", "afiniti", "northbay", "devsinc", "purelogics", "curemd"], ["ai-ml-engineer-intern", "junior-ai-engineer", "data-scientist", "python-developer"]),
    "web": (["arbisoft", "tkxel", "10pearls", "devsinc", "purelogics", "cubix", "vteams", "nextbridge", "systems-limited"], ["frontend-developer", "full-stack-developer", "backend-developer", "mobile-app-developer"]),
    "cloud": (["northbay", "10pearls", "techlogix", "contour-software", "purelogics", "vteams", "confiz"], ["backend-developer", "full-stack-developer", "python-developer"]),
    "qa": (["kualitatem"], ["python-developer", "backend-developer", "full-stack-developer"]),
    "mobile": (["tkxel", "cubix", "mindstorm-studios", "10pearls", "devsinc", "purelogics", "vteams", "nextbridge"], ["mobile-app-developer", "frontend-developer", "full-stack-developer"]),
    "game": (["mindstorm-studios"], ["mobile-app-developer", "backend-developer"]),
}
ITEMS: list[dict] = []


def _add(kind, cat, diff, prompt, correct, wrong, expl, grp, topics):
    assert correct not in wrong and len(set(wrong)) == len(wrong) and 2 <= len(wrong) <= 4, (prompt[:50], correct, wrong)
    n = len(ITEMS)
    opts = list(wrong)
    pos = n % (len(wrong) + 1)
    opts.insert(pos, correct)
    comp, roles = GROUPS[grp]
    ITEMS.append({"kind": kind, "category": cat, "difficulty": diff, "prompt": prompt, "options": opts, "answer_index": pos, "explanation": expl, "companies": comp, "roles": roles, "topics": topics})


def mc(cat, diff, prompt, correct, wrong, expl, grp="all", topics=None):
    _add("mcq", cat, diff, prompt, correct, wrong, expl, grp, topics or [cat])


def py_out(diff, code, wrong, expl, grp="all", topics=None, cat="python"):
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=10)
    assert r.returncode == 0, (code, r.stderr)
    _add("output", cat, diff, "What does this Python program print?\n\n```python\n" + code + "\n```", r.stdout.strip(), wrong, expl, grp, topics or [cat])


def js_out(diff, code, wrong, expl, grp="web", topics=None):
    r = subprocess.run(["node", "-e", code], capture_output=True, text=True, timeout=10)
    assert r.returncode == 0, (code, r.stderr)
    _add("output", "javascript", diff, "What does this JavaScript program print?\n\n```javascript\n" + code + "\n```", r.stdout.strip(), wrong, expl, grp, topics or ["javascript"])


def sql_out(diff, setup, query, wrong, expl, topics=None):
    con = sqlite3.connect(":memory:")
    con.executescript(setup)
    got = con.execute(query).fetchall()
    _add("output", "sql", diff, "Given this table:\n\n```sql\n" + setup.strip() + "\n```\n\nWhat does this query return?\n\n```sql\n" + query + "\n```", str(got), wrong, expl, "all", topics or ["sql"])


def calc(diff, prompt, expr, wrong, expl, grp="all"):
    v = eval(expr)  # noqa: S307 - trusted authoring expression
    v = int(v) if float(v) == int(v) else round(v, 2)
    _add("mcq", "logic", diff, prompt, str(v), [str(w) for w in wrong], expl, grp, ["logic"])


def write(name="screening"):
    out = []
    for i, it in enumerate(ITEMS, 1):
        out.append({"slug": f"scr-{i:03d}-{it['category']}", **it, "ideal_answer": "", "key_points": [], "follow_ups": [], "source_label": "company_focused_practice", "source_note": "", "enabled": True})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps({"questions": out}, indent=1, ensure_ascii=False), encoding="utf-8")
    return out
