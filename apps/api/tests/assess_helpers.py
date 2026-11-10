"""A scripted stand-in for the AI that writes and checks questions. It is deterministic and never touches the network."""

import hashlib
import json
import re
from collections.abc import Callable


def word(k: int, i: int) -> str:
    return hashlib.sha256(f"{k}-{i}".encode()).hexdigest()[:9]


TEMPLATES = [
    "Considering {a} in a {skill} project at stage {b}, which statement about {c} is accurate?",
    "A teammate working with {skill} reports problem {a} after change {b}; what explains {c} best?",
    "When reviewing {skill} code related to {a}, which practice most improves {c} under {b}?",
    "Which approach to {c} is most appropriate for a {skill} service handling {a} and {b}?",
    "In {skill}, what is the main reason to care about {a} when {b} affects {c}?",
]
SHORT = [
    "Explain how you would handle {a} with {skill} when {b} and {c} both matter, and name the trade-offs.",
    "Describe your approach to {a} in a {skill} project, including how you would check {b} and {c}.",
]


class ScriptedAI:
    name = "fake"
    model = "fake-model"

    def __init__(
        self,
        mutate: Callable[[dict, str, int], dict | None] | None = None,
        verify: Callable[[dict, int | None], dict] | None = None,
        fail_generate: Exception | None = None,
    ):
        self.mutate, self.verify_hook, self.fail_generate = mutate, verify, fail_generate
        self.calls: list[list[dict]] = []
        self.counter = 0
        self.keys: dict[str, int | None] = {}
        self.categories: dict[str, str] = {}

    # ---- LLMProvider ----
    def complete_json(self, messages):
        self.calls.append(messages)
        system = messages[0]["content"]
        if "write practice interview questions" in system:
            if self.fail_generate:
                raise self.fail_generate
            return self._generate(messages[1]["content"])
        if "check practice interview questions" in system:
            return self._verify(messages[1]["content"])
        raise AssertionError("unexpected prompt")

    def _generate(self, user: str) -> str:
        ask = int(re.search(r"Write exactly (\d+) questions", user).group(1))
        mcq = int(re.search(r"about (\d+) mcq", user).group(1))
        cat = re.search(r"Category: (\w+)", user).group(1)
        skills = [s.strip() for s in re.search(r"Focus skills: (.*)", user).group(1).split(",") if s.strip()] or ["python"]
        out = []
        for n in range(ask):
            self.counter += 1
            k = self.counter
            skill = skills[n % len(skills)]
            a, b, c = word(k, 1), word(k, 2), word(k, 3)
            if n < mcq:
                opts = [f"{word(k, 10 + j)} {word(k, 20 + j)}" for j in range(4)]
                q = {
                    "type": "mcq",
                    "prompt": TEMPLATES[k % 5].format(a=a, b=b, c=c, skill=skill),
                    "options": opts,
                    "correct_index": k % 4,
                    "reference_points": [],
                    "explanation": f"Because {word(k, 30)} follows from {skill} fundamentals.",
                    "topic": f"{skill} fundamentals",
                    "skills": [skill],
                    "difficulty": ["easy", "medium", "hard"][k % 3],
                    "informed_by": [],
                }
            else:
                q = {
                    "type": "short_answer",
                    "prompt": SHORT[k % 2].format(a=a, b=b, c=c, skill=skill),
                    "options": [],
                    "correct_index": None,
                    "reference_points": [f"Mention {word(k, 40)} and why it matters", f"Discuss the trade-off around {word(k, 41)}"],
                    "explanation": f"A strong answer covers {word(k, 42)} for {skill}.",
                    "topic": f"{skill} design",
                    "skills": [skill],
                    "difficulty": "medium",
                    "informed_by": [],
                }
            if cat == "company_informed":
                q["informed_by"] = [1]
            if self.mutate:
                q = self.mutate(q, cat, k)
                if q is None:
                    continue
            self.keys[q["prompt"]] = q.get("correct_index")
            self.categories[q["prompt"]] = cat
            out.append(q)
        return json.dumps({"questions": out})

    def _verify(self, user: str) -> str:
        items = json.loads(user)
        answers = []
        for it in items:
            claimed = self.keys.get(it["question"])
            a = {"id": it["id"], "choice": claimed if it["type"] == "mcq" else None, "ambiguous": False, "clear": True}
            if self.verify_hook:
                a = self.verify_hook(a, claimed)
            answers.append(a)
        return json.dumps({"answers": answers})
