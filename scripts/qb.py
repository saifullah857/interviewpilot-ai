"""Tiny helper for writing question-bank files. Every question here is `company_focused_practice`: written for a company's technology
focus. None is presented as a real interview question of that company."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "questions"


def q(cat, diff, topics, prompt, ideal, points, follow, kind="technical", roles=None):
    return {"cat": cat, "diff": diff, "topics": topics, "prompt": prompt, "ideal": ideal, "points": points, "follow": follow, "kind": kind, "roles": roles}


def write(company, default_roles, items):
    assert len(items) == 25, (company, len(items))
    out = []
    for i, it in enumerate(items, 1):
        out.append({
            "slug": f"{company}-tech-{i:02d}", "kind": it["kind"], "category": it["cat"], "difficulty": it["diff"], "roles": it["roles"] or default_roles,
            "companies": [company], "topics": it["topics"], "prompt": it["prompt"], "ideal_answer": it["ideal"], "key_points": it["points"], "follow_ups": it["follow"],
            "source_label": "company_focused_practice", "source_note": "", "enabled": True,
        })
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{company}.json").write_text(json.dumps({"company": company, "questions": out}, indent=1, ensure_ascii=False), encoding="utf-8")
    return out
