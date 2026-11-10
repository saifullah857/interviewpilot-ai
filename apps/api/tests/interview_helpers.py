"""A scripted stand-in for the AI interviewer and evaluator. Deterministic; never touches the network.
It reads the same prompts the real model would, so tests also prove what the prompts contain."""

import hashlib
import json
import re
from collections.abc import Callable

ANSWER = re.compile(r"<candidate_answer>\n(.*?)\n</candidate_answer>", re.DOTALL)
ANSWER_TURN = re.compile(r"\[(\d+)\] Candidate:\n<candidate_answer>")


def word(k: int, i: int) -> str:
    return hashlib.sha256(f"{k}-{i}".encode()).hexdigest()[:9]


class ScriptedInterviewer:
    name = "fake"
    model = "fake-model"

    def __init__(self, turn_hook: Callable[[str, int], dict | None] | None = None, eval_hook: Callable[[dict, str], dict] | None = None, follow_ups: bool = True):
        self.turn_hook, self.eval_hook, self.follow_ups = turn_hook, eval_hook, follow_ups
        self.calls: list[list[dict]] = []
        self.turn_prompts: list[str] = []
        self.eval_prompts: list[str] = []
        self.k = 0

    def complete_json(self, messages):
        self.calls.append(messages)
        system, user = messages[0]["content"], messages[1]["content"]
        if "practice technical interviewer" in system:
            self.turn_prompts.append(user)
            return self._turn(user)
        if "You evaluate a practice technical interview" in system:
            self.eval_prompts.append(user)
            return self._eval(user)
        raise AssertionError("unexpected prompt")

    def _turn(self, user: str) -> str:
        self.k += 1
        k = self.k
        if self.turn_hook:
            custom = self.turn_hook(user, k)
            if custom is not None:
                return json.dumps(custom)
        answers = ANSWER.findall(user)
        slots_left = "No main questions remain" not in user
        can_follow = "Choose 'follow_up' if the last answer" in user and bool(answers) and self.follow_ups
        if not slots_left:
            if "Choose 'follow_up' only if worthwhile" in user and bool(answers) and self.follow_ups:
                pick = next(iter(re.findall(r"[a-z]{6,}", answers[-1].lower())), None)
                if pick:
                    return json.dumps({"kind": "follow_up", "message": f"You mentioned {pick}; why did you choose that approach, and what would you change?", "topic": "Follow-up", "informed_by": []})
            return json.dumps({"kind": "wrap_up", "message": "", "topic": "", "informed_by": []})
        if can_follow:
            pick = next(iter(re.findall(r"[a-z]{6,}", answers[-1].lower())), "that")
            variants = [
                f"You said {pick} earlier; why did you choose that, and which trade-offs did you weigh?",
                f"How would you test and debug the {pick} part if it started failing under heavy load in production?",
                f"If a teammate challenged your {pick} decision, which evidence would you show them to defend it?",
            ]
            return json.dumps({"kind": "follow_up", "message": variants[k % 3], "topic": "Follow-up", "informed_by": []})
        informed = [1, 99] if "<company_evidence>" in user else []
        a, b, c = word(k, 1), word(k, 2), word(k, 3)
        return json.dumps({"kind": "question", "message": f"Considering {a} and {b}, how would you approach {c} in a small service you maintain yourself?", "topic": f"Topic {k}", "informed_by": informed})

    def _eval(self, user: str) -> str:
        positions = [int(p) for p in ANSWER_TURN.findall(user)]
        ev = positions[:2] + [999]  # 999 is a made-up turn number: the server must drop it
        crit = {"score": 3, "rationale": "Clear explanation with a concrete example from the project.", "evidence_turns": ev}
        data = {
            "technical_correctness": crit,
            "reasoning": {**crit, "score": 2},
            "clarity": {**crit, "score": 4, "evidence_turns": positions[:1]},
            "specificity": {**crit, "score": 1, "evidence_turns": []},
            "strengths": ["Explained the design choice clearly."],
            "improvements": ["Add how you would test the change."],
            "per_answer": ([{"turn": positions[0], "note": "Good detail on your own contribution.", "stronger_answer_hint": "Name a measurable result."}] if positions else [])
            + [{"turn": 424242, "note": "Note about a turn that does not exist.", "stronger_answer_hint": ""}],
        }
        if self.eval_hook:
            data = self.eval_hook(data, user)
        return json.dumps(data)
