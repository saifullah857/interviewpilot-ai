"""Deliberately WRONG solutions (trusted test fixtures). The hidden tests must catch every one of them.
`slow=True` marks a correct-but-too-slow solution that must time out."""

MUTANTS: dict[str, list[dict]] = {
    "two-sum": [
        {
            "name": "indices swapped",
            "code": "def two_sum(nums, target):\n    seen = {}\n    for j, x in enumerate(nums):\n        if target - x in seen:\n            return [j, seen[target - x]]\n        seen[x] = j\n",
        },
        {
            "name": "reuses the same element",
            "code": "def two_sum(nums, target):\n    for j, x in enumerate(nums):\n        if target - x in nums:\n            return [nums.index(target - x), j]\n",
        },
        {
            "name": "pair-by-pair search (too slow)",
            "slow": True,
            "code": "def two_sum(nums, target):\n    for i in range(len(nums)):\n        for j in range(i + 1, len(nums)):\n            if nums[i] + nums[j] == target:\n                return [i, j]\n",
        },
    ],
    "valid-parentheses": [
        {
            "name": "only counts brackets",
            "code": "def is_valid(s):\n    return s.count('(') == s.count(')') and s.count('[') == s.count(']') and s.count('{') == s.count('}')\n",
        },
        {
            "name": "no empty-stack check",
            "code": "def is_valid(s):\n    pairs = {')': '(', ']': '[', '}': '{'}\n    stack = []\n    for ch in s:\n        if ch in pairs:\n            if stack.pop() != pairs[ch]:\n                return False\n        else:\n            stack.append(ch)\n    return not stack\n",
        },
    ],
    "group-anagrams": [
        {
            "name": "sorts words inside groups",
            "code": "def group_anagrams(words):\n    groups = {}\n    for w in words:\n        groups.setdefault(''.join(sorted(w)), []).append(w)\n    return [sorted(g) for g in groups.values()]\n",
        },
        {
            "name": "ignores letter counts",
            "code": "def group_anagrams(words):\n    groups = {}\n    for w in words:\n        groups.setdefault(frozenset(w), []).append(w)\n    return list(groups.values())\n",
        },
    ],
    "merge-intervals": [
        {
            "name": "does not sort",
            "code": "def merge_intervals(intervals):\n    out = []\n    for s, e in intervals:\n        if out and s <= out[-1][1]:\n            out[-1][1] = max(out[-1][1], e)\n        else:\n            out.append([s, e])\n    return out\n",
        },
        {
            "name": "touching intervals are not merged",
            "code": "def merge_intervals(intervals):\n    out = []\n    for s, e in sorted(intervals):\n        if out and s < out[-1][1]:\n            out[-1][1] = max(out[-1][1], e)\n        else:\n            out.append([s, e])\n    return out\n",
        },
    ],
    "top-k-frequent": [
        {
            "name": "ties: larger value first",
            "code": "def top_k_frequent(nums, k):\n    from collections import Counter\n    c = Counter(nums)\n    return sorted(c, key=lambda v: (-c[v], -v))[:k]\n",
        },
        {
            "name": "ties: insertion order",
            "code": "def top_k_frequent(nums, k):\n    from collections import Counter\n    return [v for v, _ in Counter(nums).most_common(k)]\n",
        },
    ],
    "binary-search": [
        {
            "name": "skips the last element",
            "code": "def search(nums, target):\n    lo, hi = 0, len(nums) - 1\n    while lo < hi:\n        mid = (lo + hi) // 2\n        if nums[mid] == target:\n            return mid\n        if nums[mid] < target:\n            lo = mid + 1\n        else:\n            hi = mid - 1\n    return -1\n",
        },
        {
            "name": "crashes on an empty list",
            "code": "def search(nums, target):\n    if target > nums[-1]:\n        return -1\n    return nums.index(target) if target in nums else -1\n",
        },
    ],
    "word-frequency": [
        {
            "name": "case sensitive",
            "code": "def word_frequency(text):\n    import re\n    from collections import Counter\n    c = Counter(re.findall(r'[A-Za-z]+', text))\n    return [[w, n] for w, n in sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))]\n",
        },
        {
            "name": "keeps apostrophes inside words",
            "code": 'def word_frequency(text):\n    import re\n    from collections import Counter\n    c = Counter(re.findall(r"[a-z\']+", text.lower()))\n    return [[w, n] for w, n in sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))]\n',
        },
    ],
    "longest-unique-substring": [
        {"name": "counts distinct characters", "code": "def length_of_longest_substring(s):\n    return len(set(s))\n"},
        {
            "name": "restarts the window at the wrong place",
            "code": "def length_of_longest_substring(s):\n    last, start, best = {}, 0, 0\n    for i, ch in enumerate(s):\n        if ch in last:\n            start = i\n        last[ch] = i\n        best = max(best, i - start + 1)\n    return best\n",
        },
    ],
    "classification-metrics": [
        {
            "name": "no zero-division guard",
            "code": "def classification_metrics(y_true, y_pred):\n    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)\n    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)\n    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)\n    p = tp / (tp + fp)\n    r = tp / (tp + fn)\n    return [round(p, 4), round(r, 4), round(2 * p * r / (p + r), 4)]\n",
        },
        {
            "name": "f1 as a plain average",
            "code": "def classification_metrics(y_true, y_pred):\n    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)\n    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)\n    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)\n    p = tp / (tp + fp) if tp + fp else 0.0\n    r = tp / (tp + fn) if tp + fn else 0.0\n    return [round(p, 4), round(r, 4), round((p + r) / 2, 4)]\n",
        },
    ],
    "min-max-scale": [
        {
            "name": "no all-equal guard",
            "code": "def min_max_scale(values):\n    if not values:\n        return []\n    lo, hi = min(values), max(values)\n    return [round((x - lo) / (hi - lo), 6) for x in values]\n",
        },
        {
            "name": "forgets to round",
            "code": "def min_max_scale(values):\n    if not values:\n        return []\n    lo, hi = min(values), max(values)\n    if hi == lo:\n        return [0.0] * len(values)\n    return [(x - lo) / (hi - lo) for x in values]\n",
        },
    ],
}


from tests.runner.mutants_screening import MUTANTS_SCREENING  # noqa: E402

MUTANTS.update(MUTANTS_SCREENING)

from tests.runner.mutants_advanced import MUTANTS_ADVANCED  # noqa: E402

MUTANTS.update(MUTANTS_ADVANCED)
