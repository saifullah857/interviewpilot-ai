"""Deliberately WRONG solutions for the advanced problems (trusted test fixtures). Hidden tests must catch each one."""


def m(name, code, slow=False):
    d = {"name": name, "code": code}
    if slow:
        d["slow"] = True
    return d


MUTANTS_ADVANCED = {
    "reverse-words": [
        m("splits on a single space, keeps empty words", "def reverse_words(s):\n    return ' '.join(s.split(' ')[::-1])\n"),
        m("reverses the characters", "def reverse_words(s):\n    return ' '.join(s.split())[::-1]\n"),
    ],
    "digital-root": [
        m("one pass of digit sums only", "def digital_root(n):\n    return sum(int(c) for c in str(n))\n"),
        m("n % 9 forgets the multiples of 9", "def digital_root(n):\n    return n % 9\n"),
    ],
    "caesar-cipher": [
        m("loses the case", "def caesar(text, k):\n    return ''.join(chr((ord(c) - 97 + k) % 26 + 97) if c.isalpha() else c for c in text.lower())\n"),
        m("does not wrap around", "def caesar(text, k):\n    return ''.join(chr(ord(c) + k) if c.isalpha() else c for c in text)\n"),
    ],
    "move-zeros": [
        m("sorts the numbers", "def move_zeros(nums):\n    return sorted(nums, key=lambda x: x == 0)[::1] if False else sorted(nums, key=lambda x: (x == 0, x))\n"),
        m("moves zeros to the front", "def move_zeros(nums):\n    z = [x for x in nums if x == 0]\n    return z + [x for x in nums if x != 0]\n"),
    ],
    "min-stack-ops": [
        m("keeps the global minimum after a pop", "def min_stack_ops(ops):\n    st, mn, out = [], None, []\n    for op in ops:\n        if op[0] == 'push':\n            st.append(op[1])\n            mn = op[1] if mn is None else min(mn, op[1])\n        elif op[0] == 'pop':\n            if st:\n                st.pop()\n        elif op[0] == 'top':\n            out.append(st[-1] if st else None)\n        else:\n            out.append(mn if st else None)\n    return out\n"),
        m("min returns the top", "def min_stack_ops(ops):\n    st, out = [], []\n    for op in ops:\n        if op[0] == 'push':\n            st.append(op[1])\n        elif op[0] == 'pop':\n            if st:\n                st.pop()\n        else:\n            out.append(st[-1] if st else None)\n    return out\n"),
    ],
    "linked-list-cycle": [
        m("any node without an end means a cycle", "def has_cycle(nxt, head):\n    return head != -1 and -1 not in nxt\n"),
        m("only a pointer back to the head counts", "def has_cycle(nxt, head):\n    return head != -1 and head in nxt\n"),
    ],
    "tree-level-order": [
        m("one flat list of all values", "def level_order(root):\n    out = []\n    st = [root] if root else []\n    while st:\n        n = st.pop(0)\n        out.append(n[0])\n        st += [c for c in (n[1], n[2]) if c]\n    return [out] if out else []\n"),
        m("right to left inside each level", "def level_order(root):\n    if not root:\n        return []\n    level, out = [root], []\n    while level:\n        out.append([n[0] for n in level][::-1])\n        level = [c for n in level for c in (n[1], n[2]) if c]\n    return out\n"),
    ],
    "validate-bst": [
        m("only compares with the direct children", "def is_valid_bst(root):\n    if root is None:\n        return True\n    l, r = root[1], root[2]\n    if l is not None and not l[0] < root[0]:\n        return False\n    if r is not None and not r[0] > root[0]:\n        return False\n    return is_valid_bst(l) and is_valid_bst(r)\n"),
        m("allows equal values", "def is_valid_bst(root):\n    stack = [(root, float('-inf'), float('inf'))]\n    while stack:\n        n, lo, hi = stack.pop()\n        if n is None:\n            continue\n        if not lo <= n[0] <= hi:\n            return False\n        stack.append((n[1], lo, n[0]))\n        stack.append((n[2], n[0], hi))\n    return True\n"),
    ],
    "tree-path-sum": [
        m("any node counts as the end of a path", "def has_path_sum(root, target):\n    if root is None:\n        return False\n    st = [(root, root[0])]\n    while st:\n        n, t = st.pop()\n        if t == target:\n            return True\n        for c in (n[1], n[2]):\n            if c is not None:\n                st.append((c, t + c[0]))\n    return False\n"),
        m("an empty tree with target 0 is a path", "def has_path_sum(root, target):\n    if root is None:\n        return target == 0\n    st = [(root, root[0])]\n    while st:\n        n, t = st.pop()\n        if n[1] is None and n[2] is None and t == target:\n            return True\n        for c in (n[1], n[2]):\n            if c is not None:\n                st.append((c, t + c[0]))\n    return False\n"),
    ],
    "product-except-self": [
        m("uses division", "def product_except_self(nums):\n    p = 1\n    for x in nums:\n        p *= x\n    return [p // x if x else 0 for x in nums]\n"),
        m("only the left products", "def product_except_self(nums):\n    out, left = [], 1\n    for x in nums:\n        out.append(left)\n        left *= x\n    return out\n"),
    ],
    "three-sum": [
        m("repeated triplets are kept", "def three_sum(nums):\n    a = sorted(nums)\n    out = []\n    for i in range(len(a) - 2):\n        lo, hi = i + 1, len(a) - 1\n        while lo < hi:\n            s = a[i] + a[lo] + a[hi]\n            if s < 0:\n                lo += 1\n            elif s > 0:\n                hi -= 1\n            else:\n                out.append([a[i], a[lo], a[hi]])\n                lo += 1\n                hi -= 1\n    return out\n"),
        m("stops at the first triplet for each first number", "def three_sum(nums):\n    a = sorted(nums)\n    out = []\n    for i in range(len(a) - 2):\n        if i and a[i] == a[i - 1]:\n            continue\n        lo, hi = i + 1, len(a) - 1\n        while lo < hi:\n            s = a[i] + a[lo] + a[hi]\n            if s < 0:\n                lo += 1\n            elif s > 0:\n                hi -= 1\n            else:\n                out.append([a[i], a[lo], a[hi]])\n                break\n    return out\n"),
    ],
    "daily-temperatures": [
        m("counts an equal temperature as warmer", "def daily_temperatures(temps):\n    out = [0] * len(temps)\n    st = []\n    for i, t in enumerate(temps):\n        while st and temps[st[-1]] <= t:\n            out[st[-1]] = i - st.pop()\n        st.append(i)\n    return out\n"),
        m("scans forward from every day (too slow)", "def daily_temperatures(temps):\n    out = [0] * len(temps)\n    for i in range(len(temps)):\n        for j in range(i + 1, len(temps)):\n            if temps[j] > temps[i]:\n                out[i] = j - i\n                break\n    return out\n", slow=True),
    ],
    "subarray-sum-k": [
        m("sliding window fails with negatives", "def subarray_sum(nums, k):\n    count = left = total = 0\n    for right, x in enumerate(nums):\n        total += x\n        while total > k and left <= right:\n            total -= nums[left]\n            left += 1\n        if total == k:\n            count += 1\n    return count\n"),
        m("counts each prefix sum once", "def subarray_sum(nums, k):\n    seen, total, count = {0}, 0, 0\n    for x in nums:\n        total += x\n        if total - k in seen:\n            count += 1\n        seen.add(total)\n    return count\n"),
    ],
    "container-most-water": [
        m("width off by one", "def max_area(heights):\n    lo, hi, best = 0, len(heights) - 1, 0\n    while lo < hi:\n        best = max(best, (hi - lo - 1) * min(heights[lo], heights[hi]))\n        if heights[lo] < heights[hi]:\n            lo += 1\n        else:\n            hi -= 1\n    return best\n"),
        m("uses the taller line", "def max_area(heights):\n    lo, hi, best = 0, len(heights) - 1, 0\n    while lo < hi:\n        best = max(best, (hi - lo) * max(heights[lo], heights[hi]))\n        if heights[lo] < heights[hi]:\n            lo += 1\n        else:\n            hi -= 1\n    return best\n"),
    ],
    "tree-lca": [
        m("assumes a search tree", "def lowest_common_ancestor(root, p, q):\n    n = root\n    while n:\n        if p < n[0] and q < n[0]:\n            n = n[1]\n        elif p > n[0] and q > n[0]:\n            n = n[2]\n        else:\n            return n[0]\n    return root[0]\n"),
        m("always the root", "def lowest_common_ancestor(root, p, q):\n    return root[0]\n"),
    ],
    "trapping-rain-water": [
        m("only the highest bar on the left", "def trap(heights):\n    best, water = 0, 0\n    for h in heights:\n        best = max(best, h)\n        water += best - h\n    return water\n"),
        m("counts the gap to the global maximum", "def trap(heights):\n    return sum(max(heights) - h for h in heights) if heights else 0\n"),
    ],
    "coin-change-min": [
        m("greedy with the biggest coin", "def coin_change(coins, amount):\n    n = 0\n    for c in sorted(coins, reverse=True):\n        n += amount // c\n        amount %= c\n    return n if amount == 0 else -1\n"),
        m("gives 0 when impossible", "def coin_change(coins, amount):\n    INF = amount + 1\n    b = [0] + [INF] * amount\n    for a in range(1, amount + 1):\n        for c in coins:\n            if c <= a:\n                b[a] = min(b[a], b[a - c] + 1)\n    return b[amount] if b[amount] < INF else 0\n"),
    ],
    "lis-length": [
        m("longest contiguous increasing run", "def length_of_lis(nums):\n    best = cur = 0\n    for i, x in enumerate(nums):\n        cur = cur + 1 if i and x > nums[i - 1] else 1\n        best = max(best, cur)\n    return best\n"),
        m("allows equal values", "import bisect\n\n\ndef length_of_lis(nums):\n    t = []\n    for x in nums:\n        i = bisect.bisect_right(t, x)\n        if i == len(t):\n            t.append(x)\n        else:\n            t[i] = x\n    return len(t)\n"),
    ],
    "word-ladder-length": [
        m("counts steps instead of words", "from collections import deque\n\n\ndef ladder_length(begin, end, words):\n    pool = set(words)\n    if end not in pool:\n        return 0\n    q, seen = deque([(begin, 0)]), {begin}\n    while q:\n        w, d = q.popleft()\n        if w == end:\n            return d\n        for i in range(len(w)):\n            for c in 'abcdefghijklmnopqrstuvwxyz':\n                n = w[:i] + c + w[i + 1:]\n                if n in pool and n not in seen:\n                    seen.add(n)\n                    q.append((n, d + 1))\n    return 0\n"),
        m("does not require the end word in the list", "from collections import deque\n\n\ndef ladder_length(begin, end, words):\n    pool = set(words) | {end}\n    q, seen = deque([(begin, 1)]), {begin}\n    while q:\n        w, d = q.popleft()\n        if w == end:\n            return d\n        for i in range(len(w)):\n            for c in 'abcdefghijklmnopqrstuvwxyz':\n                n = w[:i] + c + w[i + 1:]\n                if n in pool and n not in seen:\n                    seen.add(n)\n                    q.append((n, d + 1))\n    return 0\n"),
    ],
    "merge-k-sorted": [
        m("concatenates without sorting", "def merge_k_lists(lists):\n    return [x for l in lists for x in l]\n"),
        m("drops duplicates", "def merge_k_lists(lists):\n    return sorted({x for l in lists for x in l})\n"),
    ],
    "edit-distance": [
        m("counts only replacements of equal-length strings", "def edit_distance(a, b):\n    return sum(x != y for x, y in zip(a, b)) + abs(len(a) - len(b))\n"),
        m("insert and delete only", "def edit_distance(a, b):\n    prev = list(range(len(b) + 1))\n    for i in range(1, len(a) + 1):\n        cur = [i] + [0] * len(b)\n        for j in range(1, len(b) + 1):\n            cur[j] = prev[j - 1] if a[i - 1] == b[j - 1] else min(prev[j], cur[j - 1]) + 1\n        prev = cur\n    return prev[-1]\n"),
    ],
    "n-queens-count": [
        m("forgets the diagonals", "import math\n\n\ndef count_queens(n):\n    return math.factorial(n)\n"),
        m("checks only one diagonal", "def count_queens(n):\n    cols, d1 = set(), set()\n    def place(r):\n        if r == n:\n            return 1\n        t = 0\n        for c in range(n):\n            if c in cols or r - c in d1:\n                continue\n            cols.add(c)\n            d1.add(r - c)\n            t += place(r + 1)\n            cols.remove(c)\n            d1.remove(r - c)\n        return t\n    return place(0)\n"),
    ],
    "longest-valid-parentheses": [
        m("counts every matched pair", "def longest_valid(s):\n    open_, pairs = 0, 0\n    for ch in s:\n        if ch == '(':\n            open_ += 1\n        elif open_:\n            open_ -= 1\n            pairs += 1\n    return pairs * 2\n"),
        m("resets only when closing exceeds opening, forgets trailing opens", "def longest_valid(s):\n    best = o = c = 0\n    for ch in s:\n        o, c = (o + 1, c) if ch == '(' else (o, c + 1)\n        if o == c:\n            best = max(best, 2 * c)\n        elif c > o:\n            o = c = 0\n    return best\n"),
    ],
    "sliding-window-max": [
        m("minimum instead of maximum", "def max_sliding_window(nums, k):\n    return [min(nums[i:i + k]) for i in range(len(nums) - k + 1)]\n"),
        m("last window is missing", "def max_sliding_window(nums, k):\n    return [max(nums[i:i + k]) for i in range(len(nums) - k)]\n"),
    ],
}
