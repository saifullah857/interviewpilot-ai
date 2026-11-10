"""Regenerates data/coding/problems.json from the problem definitions below.
Expected outputs are computed from the reference solutions (trusted code written for this project). The test-suite then checks
every reference against the harness, and checks that deliberately wrong solutions are caught by the hidden tests.
Run from the repository root:  python scripts/build_coding_problems.py"""
import copy
import json
import random
import sys
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "data" / "coding" / "problems.json"
PROBLEMS: list[dict] = []


def problem(**kw):
    PROBLEMS.append(kw)


rng = random.Random(7)

# ---------------------------------------------------------------- 1. two sum
big = rng.sample(range(-10**9, 10**9), 10000)
big_target = big[9500] + big[9876]  # late in the list, so an O(n^2) search is slow
assert sum(Counter(big)[big_target - x] for x in big) == 2  # exactly one pair (counted from both sides)
problem(
    slug="two-sum", title="Two Sum", difficulty="easy", minutes=15, topics=["arrays", "hash maps"], roles=["python-developer", "ai-ml-engineer-intern", "backend-developer", "full-stack-developer", "frontend-developer", "mobile-app-developer"],
    statement="Given a list of integers `nums` and an integer `target`, return the indices `[i, j]` of the two numbers that add up to `target`, with `i < j`.\n\nExactly one such pair exists. You may not use the same element twice.",
    constraints=["2 <= len(nums) <= 10000", "-10^9 <= nums[k], target <= 10^9", "Exactly one valid pair exists", "Return the indices in increasing order: [i, j] with i < j"],
    entry_point="two_sum", signature="def two_sum(nums, target):",
    reference="def two_sum(nums, target):\n    seen = {}\n    for j, x in enumerate(nums):\n        if target - x in seen:\n            return [seen[target - x], j]\n        seen[x] = j\n",
    visible=[[[2, 7, 11, 15], 9], [[3, 2, 4], 6], [[3, 3], 6]],
    hidden=[[[-1, -2, -3, -4, -5], -8], [[0, 4, 3, 0], 0], [[1, 5, 5, 9], 10], [[1000000000, -999999999, 5], 1], [[1, 2], 3], [big, big_target]],
    examples=["`nums[0] + nums[1] = 2 + 7 = 9`, so the answer is `[0, 1]`.", "`nums[1] + nums[2] = 2 + 4 = 6`."],
    complexity={"time": "O(n)", "space": "O(n)"},
    approach="Scan once, remembering each value's index in a dictionary. For each number, check whether its complement (target minus the number) was already seen. This is O(n) instead of the O(n^2) pair-by-pair search.",
)

# ---------------------------------------------------------------- 2. valid parentheses
problem(
    slug="valid-parentheses", title="Valid Parentheses", difficulty="easy", minutes=15, topics=["stacks", "strings"], roles=["python-developer", "backend-developer", "full-stack-developer", "frontend-developer", "mobile-app-developer"],
    statement="Given a string `s` containing only the characters `(`, `)`, `[`, `]`, `{` and `}`, return `True` if the brackets are valid and `False` otherwise.\n\nA string is valid when every opening bracket is closed by the same type of bracket, in the correct order. The empty string is valid.",
    constraints=["0 <= len(s) <= 10000", "s contains only ()[]{}"],
    entry_point="is_valid", signature="def is_valid(s):",
    reference="def is_valid(s):\n    pairs = {')': '(', ']': '[', '}': '{'}\n    stack = []\n    for ch in s:\n        if ch in pairs:\n            if not stack or stack.pop() != pairs[ch]:\n                return False\n        else:\n            stack.append(ch)\n    return not stack\n",
    visible=[["()"], ["()[]{}"], ["(]"]],
    hidden=[[""], ["([{}])"], ["([)]"], ["((("], [")("], ["{[]}"], ["(" * 5000 + ")" * 5000], ["()" * 5000], ["]"]],
    examples=["`()[]{}` is valid: every bracket is closed in order.", "`(]` is not valid: `]` does not match `(`."],
    complexity={"time": "O(n)", "space": "O(n)"},
    approach="Push each opening bracket on a stack. For a closing bracket, the top of the stack must be its matching opener (and the stack must not be empty). At the end the stack must be empty.",
)

# ---------------------------------------------------------------- 3. group anagrams
problem(
    slug="group-anagrams", title="Group Anagrams", difficulty="medium", minutes=25, topics=["hash maps", "strings", "sorting"], roles=["python-developer", "junior-ai-engineer", "backend-developer", "full-stack-developer", "frontend-developer", "mobile-app-developer"],
    statement="Given a list of lowercase words, group the words that are anagrams of each other and return the groups as a list of lists.\n\nOrdering is fixed so the answer is unique: inside a group, keep the words in their original order; order the groups by where their first word appears in the input. Duplicate words are kept.",
    constraints=["0 <= len(words) <= 2000", "Each word has 0 to 20 lowercase letters a-z", "Two words are anagrams when they contain the same letters the same number of times"],
    entry_point="group_anagrams", signature="def group_anagrams(words):",
    reference="def group_anagrams(words):\n    groups = {}\n    for w in words:\n        groups.setdefault(''.join(sorted(w)), []).append(w)\n    return list(groups.values())\n",
    visible=[[["eat", "tea", "tan", "ate", "nat", "bat"]], [["a"]], [[""]]],
    hidden=[[["abc", "bca", "cab", "xyz", "zyx", "abc"]], [["listen", "silent", "enlist", "google", "gogole"]], [["ab", "ba", "ab"]], [["a", "b", "a", "b"]], [[]], [["aab", "aba", "baa", "abb"]], [["".join(rng.sample("abcdefgh", 8)) for _ in range(2000)]]],
    examples=["`eat`, `tea`, `ate` are anagrams, so they form the first group in input order.", "`[\"a\"]` gives `[[\"a\"]]`."],
    complexity={"time": "O(n * k log k)", "space": "O(n * k)"},
    approach="Use the sorted letters of each word as a dictionary key; words with the same key are anagrams. A dict keeps first-seen order, which gives the required group order.",
)

# ---------------------------------------------------------------- 4. merge intervals
problem(
    slug="merge-intervals", title="Merge Intervals", difficulty="medium", minutes=25, topics=["sorting", "arrays"], roles=["python-developer", "data-scientist", "backend-developer", "full-stack-developer", "frontend-developer", "mobile-app-developer"],
    statement="Given a list of intervals `[start, end]` (with `start <= end`), merge all overlapping intervals and return the result sorted by `start`.\n\nTwo intervals overlap when they share at least one point, so `[1, 4]` and `[4, 5]` merge into `[1, 5]`. The input may be unsorted.",
    constraints=["0 <= len(intervals) <= 5000", "-10^6 <= start <= end <= 10^6", "Return a new list sorted by start; merged intervals do not overlap or touch"],
    entry_point="merge_intervals", signature="def merge_intervals(intervals):",
    reference="def merge_intervals(intervals):\n    out = []\n    for s, e in sorted(intervals):\n        if out and s <= out[-1][1]:\n            out[-1][1] = max(out[-1][1], e)\n        else:\n            out.append([s, e])\n    return out\n",
    visible=[[[[1, 3], [2, 6], [8, 10], [15, 18]]], [[[1, 4], [4, 5]]], [[[1, 4]]]],
    hidden=[[[]], [[[5, 6], [1, 2], [2, 3]]], [[[1, 10], [2, 3], [4, 5]]], [[[1, 2], [3, 4]]], [[[-5, -1], [-3, 2]]], [[[2, 3], [2, 2]]], [[[1, 4], [0, 0]]], [rng.sample([[i * 2, i * 2 + 1] for i in range(5000)], 5000)]],
    examples=["`[1, 3]` and `[2, 6]` overlap, so they merge into `[1, 6]`.", "`[1, 4]` and `[4, 5]` touch at 4, so they merge into `[1, 5]`."],
    complexity={"time": "O(n log n)", "space": "O(n)"},
    approach="Sort by start. Walk through the intervals keeping the last merged one; if the next start is within the last end, extend it, otherwise start a new merged interval.",
)

# ---------------------------------------------------------------- 5. top k frequent
problem(
    slug="top-k-frequent", title="Top K Frequent Elements", difficulty="medium", minutes=25, topics=["hash maps", "sorting", "heaps"], roles=["python-developer", "ai-ml-engineer-intern", "junior-ai-engineer", "data-scientist", "backend-developer", "full-stack-developer", "frontend-developer", "mobile-app-developer"],
    statement="Given a list of integers `nums` and an integer `k`, return the `k` most frequent values.\n\nOrder the result by frequency (highest first). When two values have the same frequency, the smaller value comes first.",
    constraints=["1 <= len(nums) <= 10000", "-10^4 <= nums[i] <= 10^4", "1 <= k <= number of distinct values in nums"],
    entry_point="top_k_frequent", signature="def top_k_frequent(nums, k):",
    reference="def top_k_frequent(nums, k):\n    from collections import Counter\n    counts = Counter(nums)\n    return sorted(counts, key=lambda v: (-counts[v], v))[:k]\n",
    visible=[[[1, 1, 1, 2, 2, 3], 2], [[1], 1], [[4, 4, 5, 5, 6], 2]],
    hidden=[[[-1, -1, 2, 2, 3], 2], [[5, 3, 5, 3, 1, 1], 3], [[9, 9, 9, 8, 8, 7], 1], [[2, 1], 2], [[0, 0, 0, 0], 1], [[1, 2, 3, 4, 5], 5], [[rng.randint(-50, 50) for _ in range(10000)], 10], [[i % 2500 for i in range(10000)], 100]],
    examples=["`1` appears 3 times and `2` appears 2 times, so `[1, 2]`.", "`4` and `5` both appear twice; the smaller value `4` comes first."],
    complexity={"time": "O(n log n)", "space": "O(n)"},
    approach="Count occurrences, then sort the distinct values by (-count, value) and take the first k. A heap gives O(n log k).",
)

# ---------------------------------------------------------------- 6. binary search
problem(
    slug="binary-search", title="Binary Search", difficulty="easy", minutes=15, topics=["searching", "arrays"], roles=["python-developer", "backend-developer", "full-stack-developer", "frontend-developer", "mobile-app-developer"],
    statement="Given a list `nums` sorted in ascending order with no duplicates, and an integer `target`, return the index of `target` in `nums`, or `-1` if it is not present.\n\nYour solution should run in O(log n) time. (The automatic tests check correctness; the expected complexity is explained after you finish.)",
    constraints=["0 <= len(nums) <= 100000", "nums is sorted ascending and contains distinct integers", "Return -1 when target is absent"],
    entry_point="search", signature="def search(nums, target):",
    reference="def search(nums, target):\n    lo, hi = 0, len(nums) - 1\n    while lo <= hi:\n        mid = (lo + hi) // 2\n        if nums[mid] == target:\n            return mid\n        if nums[mid] < target:\n            lo = mid + 1\n        else:\n            hi = mid - 1\n    return -1\n",
    visible=[[[-1, 0, 3, 5, 9, 12], 9], [[-1, 0, 3, 5, 9, 12], 2], [[5], 5]],
    hidden=[[[], 1], [[1, 2], 2], [[1, 2], 1], [[1, 3, 5, 7], 7], [[1, 3, 5, 7], 0], [[1, 3, 5, 7], 8], [list(range(0, 2000, 2)), 1998], [list(range(0, 2000, 2)), 1999]],
    examples=["`9` is at index 4.", "`2` is not in the list, so the answer is `-1`."],
    complexity={"time": "O(log n)", "space": "O(1)"},
    approach="Keep a window [lo, hi]. Compare the middle element with the target and discard the half that cannot contain it. Be careful with the loop condition so the last remaining element is checked.",
)

# ---------------------------------------------------------------- 7. word frequency
problem(
    slug="word-frequency", title="Word Frequency", difficulty="easy", minutes=15, topics=["strings", "hash maps", "sorting"], roles=["python-developer", "ai-ml-engineer-intern", "junior-ai-engineer", "data-scientist", "backend-developer", "full-stack-developer", "frontend-developer", "mobile-app-developer"],
    statement="Given a string `text`, count how often each word appears and return a list of `[word, count]` pairs.\n\nA word is a maximal run of ASCII letters (a-z, A-Z). Everything else (digits, spaces, punctuation, apostrophes) separates words. Words are compared in lowercase. Sort the pairs by count (highest first), then by word alphabetically.",
    constraints=["0 <= len(text) <= 30000", "Only ASCII letters form words, so `it's` is the two words `it` and `s`", "Return an empty list when there are no words"],
    entry_point="word_frequency", signature="def word_frequency(text):",
    reference="def word_frequency(text):\n    import re\n    from collections import Counter\n    counts = Counter(w.lower() for w in re.findall(r'[A-Za-z]+', text))\n    return [[w, c] for w, c in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))]\n",
    visible=[["the cat and the hat"], ["Hello, hello! HELLO?"], [""]],
    hidden=[["It's a dog's life"], ["one1two2three"], ["a a b b c"], ["123 456"], ["Python python PYTHON java"], ["x" * 20000 + " " + "y " * 5000], ["The quick brown fox. The lazy dog! the end?"]],
    examples=["`the` appears twice; the other words once each, in alphabetical order.", "All three spellings are the same word `hello`."],
    complexity={"time": "O(n + m log m)", "space": "O(m)"},
    approach="Extract words with a regular expression, lowercase them, count with a Counter, then sort by (-count, word).",
)

# ---------------------------------------------------------------- 8. longest unique substring
problem(
    slug="longest-unique-substring", title="Longest Substring Without Repeating Characters", difficulty="medium", minutes=25, topics=["strings", "sliding window", "hash maps"], roles=["python-developer", "ai-ml-engineer-intern", "backend-developer", "full-stack-developer", "frontend-developer", "mobile-app-developer"],
    statement="Given a string `s`, return the length of the longest substring that contains no repeated character.\n\nA substring is a contiguous part of the string.",
    constraints=["0 <= len(s) <= 100000", "s may contain any printable ASCII characters, including spaces"],
    entry_point="length_of_longest_substring", signature="def length_of_longest_substring(s):",
    reference="def length_of_longest_substring(s):\n    last, start, best = {}, 0, 0\n    for i, ch in enumerate(s):\n        if ch in last and last[ch] >= start:\n            start = last[ch] + 1\n        last[ch] = i\n        best = max(best, i - start + 1)\n    return best\n",
    visible=[["abcabcbb"], ["bbbbb"], ["pwwkew"]],
    hidden=[[""], [" "], ["au"], ["dvdf"], ["abba"], ["tmmzuxt"], ["aabbcc"], ["aabbccdd"], ["a" * 10000], ["abcdefghijklmnopqrstuvwxyz" * 400]],
    examples=["`abc` is the longest run without repeats, so the answer is `3`.", "`wke` has length 3; `pwke` is not contiguous."],
    complexity={"time": "O(n)", "space": "O(min(n, alphabet))"},
    approach="Slide a window. Remember the last index of every character; when a character repeats inside the window, move the window start just past its previous position.",
)

# ---------------------------------------------------------------- 9. classification metrics
problem(
    slug="classification-metrics", title="Precision, Recall and F1", difficulty="easy", minutes=15, topics=["machine learning", "evaluation", "math"], roles=["ai-ml-engineer-intern", "junior-ai-engineer", "data-scientist"],
    statement="Given two equal-length lists of 0/1 labels, `y_true` (the real labels) and `y_pred` (the predictions), compute precision, recall and F1 for the positive class `1`. Return `[precision, recall, f1]`, each rounded to 4 decimal places with Python's `round()`.\n\nprecision = TP / (TP + FP), recall = TP / (TP + FN), f1 = 2 * precision * recall / (precision + recall). If a denominator is 0, that value is `0.0` (so f1 is `0.0` when precision + recall is 0).",
    constraints=["1 <= len(y_true) == len(y_pred) <= 10000", "Every label is 0 or 1", "TP = predicted 1 and truly 1; FP = predicted 1 but truly 0; FN = predicted 0 but truly 1"],
    entry_point="classification_metrics", signature="def classification_metrics(y_true, y_pred):",
    reference="def classification_metrics(y_true, y_pred):\n    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)\n    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)\n    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)\n    precision = tp / (tp + fp) if tp + fp else 0.0\n    recall = tp / (tp + fn) if tp + fn else 0.0\n    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0\n    return [round(precision, 4), round(recall, 4), round(f1, 4)]\n",
    visible=[[[1, 0, 1, 1, 0], [1, 0, 0, 1, 1]], [[1, 1, 1], [1, 1, 1]], [[0, 0], [0, 0]]],
    hidden=[[[1, 0], [0, 1]], [[1, 1, 0, 0], [1, 0, 0, 0]], [[0, 1], [1, 1]], [[1], [0]], [[0, 0, 0, 1], [1, 1, 1, 1]], [[i % 2 for i in range(10000)], [(i // 2) % 2 for i in range(10000)]], [[1, 0, 1, 0, 1, 0, 1], [1, 1, 1, 0, 0, 0, 1]]],
    examples=["TP=2, FP=1, FN=1, so precision, recall and F1 are all 2/3 = 0.6667.", "With no positives at all, every value is `0.0`."],
    complexity={"time": "O(n)", "space": "O(1)"},
    approach="Count true positives, false positives and false negatives in one pass, then apply the formulas, guarding every division against a zero denominator.",
    tolerance=1e-9,
)

# ---------------------------------------------------------------- 10. min-max scaling
problem(
    slug="min-max-scale", title="Min-Max Scaling", difficulty="easy", minutes=15, topics=["data preprocessing", "math"], roles=["ai-ml-engineer-intern", "junior-ai-engineer", "data-scientist"],
    statement="Scale a list of numbers to the range 0 to 1 with min-max scaling: `(x - min) / (max - min)`. Return a new list with each value rounded to 6 decimal places using Python's `round()`.\n\nIf all values are equal (so `max == min`), return `0.0` for every value. An empty list gives an empty list.",
    constraints=["0 <= len(values) <= 10000", "Values are integers or floats", "Return floats, in the original order"],
    entry_point="min_max_scale", signature="def min_max_scale(values):",
    reference="def min_max_scale(values):\n    if not values:\n        return []\n    lo, hi = min(values), max(values)\n    if hi == lo:\n        return [0.0] * len(values)\n    return [round((x - lo) / (hi - lo), 6) for x in values]\n",
    visible=[[[1, 2, 3]], [[5, 5, 5]], [[10]]],
    hidden=[[[]], [[-2, 0, 2]], [[3, 1, 2]], [[0.1, 0.2, 0.3]], [[1, 3]], [[100, 200, 300, 400]], [[-5, -5]], [[float(i) for i in range(5000)]]],
    examples=["Min is 1 and max is 3, so the values become `[0.0, 0.5, 1.0]`.", "All values are equal, so every output is `0.0`."],
    complexity={"time": "O(n)", "space": "O(n)"},
    approach="Find the minimum and maximum once, handle the all-equal and empty cases first, then apply the formula to every value.",
    tolerance=1e-9,
)


# Focus tags / structures for the original 10 problems (the screening problems carry their own).
LEGACY = {
    "two-sum": (["hashing", "basics"], ["list", "dict", "loop"]), "valid-parentheses": (["strings", "stacks"], ["list", "loop", "condition"]),
    "group-anagrams": (["strings", "hashing", "grouping"], ["list", "dict", "loop"]), "merge-intervals": (["sorting", "simulation"], ["list", "loop", "condition"]),
    "top-k-frequent": (["hashing", "sorting", "grouping"], ["list", "dict", "loop"]), "binary-search": (["searching", "basics"], ["list", "loop", "condition"]),
    "word-frequency": (["strings", "hashing", "grouping"], ["list", "dict", "loop"]), "longest-unique-substring": (["strings", "hashing", "sorting"], ["dict", "loop", "condition"]),
    "classification-metrics": (["data-cleaning", "math-basics"], ["list", "loop", "condition"]), "min-max-scale": (["data-cleaning", "math-basics"], ["list", "loop", "condition"]),
}


def _add_screening() -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import problems_screening_a
    import problems_advanced
    import problems_screening_b

    problems_screening_a.define(problem)
    problems_screening_b.define(problem)
    problems_advanced.define(problem)


def build() -> list[dict]:
    _add_screening()
    out = []
    for p in PROBLEMS:
        ns: dict = {}
        exec(p["reference"], ns)  # noqa: S102 - trusted reference solutions written for this project
        fn = ns[p["entry_point"]]

        def case(args, ident, hidden):
            expected = json.loads(json.dumps(fn(*copy.deepcopy(args))))
            c = {"id": ident, "args": args, "expected": expected, "hidden": hidden}
            if p.get("tolerance"):
                c["tolerance"] = p["tolerance"]
            return c

        visible = [case(a, f"v{i + 1}", False) for i, a in enumerate(p["visible"])]
        hidden = [case(a, f"h{i + 1}", True) for i, a in enumerate(p["hidden"])]
        examples = [{"args": v["args"], "output": v["expected"], "explanation": e} for v, e in zip(visible, p["examples"], strict=False)]
        starter = f"{p['signature']}\n    \"\"\"Write your solution here.\"\"\"\n    pass\n"
        out.append({
            "slug": p["slug"], "title": p["title"], "difficulty": p["difficulty"], "minutes": p["minutes"], "topics": p["topics"], "roles": list(dict.fromkeys(p["roles"])),
            "statement": p["statement"], "constraints": p["constraints"], "entry_point": p["entry_point"], "signature": p["signature"], "starter_code": starter,
            "examples": examples, "visible_tests": visible, "hidden_tests": hidden, "per_test_ms": 2000, "complexity": p["complexity"],
            "approach": p["approach"], "reference_solution": p["reference"],
            "tags": p.get("tags") or LEGACY.get(p["slug"], ([], []))[0], "ds": p.get("ds") or LEGACY.get(p["slug"], ([], []))[1],
        })
    return out


if __name__ == "__main__":
    data = {"_meta": {"note": "General practice problems written for InterviewPilot AI. They are not questions from any company. Generated by scripts/build_coding_problems.py"}, "problems": build()}
    OUT.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {len(data['problems'])} problems to {OUT}")
