"""Data-structure and algorithm problems: strings, stacks, linked lists (next-pointer arrays), trees (nested [value, left, right] lists), two pointers,
dynamic programming, graphs and backtracking. Imported by build_coding_problems.py. Expected outputs come from the references."""
import random

from problems_screening_a import ALL

R = random.Random(41)


def t(v, left=None, right=None):
    return [v, left, right]


def chain(n, side=1):
    node = None
    for v in range(n, 0, -1):
        node = t(v, None, node) if side else t(v, node, None)
    return node


def rand_tree(n, lo=-50, hi=50):
    if n == 0:
        return None
    k = R.randint(0, n - 1)
    return t(R.randint(lo, hi), rand_tree(k, lo, hi), rand_tree(n - 1 - k, lo, hi))


def bst(values):
    vals = sorted(set(values))

    def build(a, b):
        if a > b:
            return None
        m = (a + b) // 2
        return t(vals[m], build(a, m - 1), build(m + 1, b))

    return build(0, len(vals) - 1)


TREE = "A tree is given as nested lists: a node is `[value, left, right]` and a missing child (or an empty tree) is `None`."


def define(problem):
    # ---------------------------------------------------------------- EASY
    problem(
        slug="reverse-words", title="Reverse the Words", difficulty="easy", minutes=10, topics=["strings"], tags=["strings", "basics"], ds=["list", "loop"], roles=ALL,
        statement="Return the words of `s` in reverse order, joined by a single space. Words are separated by one or more spaces, and the result has no leading or trailing spaces.",
        constraints=["0 <= len(s) <= 100000", "s contains letters, digits and spaces"],
        entry_point="reverse_words", signature="def reverse_words(s):",
        reference="def reverse_words(s):\n    return ' '.join(s.split()[::-1])\n",
        visible=[["the sky  is blue"], [""], ["a"]],
        hidden=[["  hello   world  "], ["one"], ["a b c d e"], [" "], ["x" * 500 + " y"], ["  a  "], [" ".join(str(i) for i in range(2000))]],
        examples=["`\"the sky  is blue\"` becomes `\"blue is sky the\"`.", "An empty string stays empty."],
        complexity={"time": "O(n)", "space": "O(n)"},
        approach="Split on whitespace (which drops empty pieces), reverse the list of words and join with one space.",
    )
    problem(
        slug="digital-root", title="Digital Root", difficulty="easy", minutes=10, topics=["math", "loops"], tags=["math-basics", "basics"], ds=["loop", "condition"], roles=ALL,
        statement="Repeatedly replace a non-negative integer `n` by the sum of its digits until only one digit is left, and return that digit. Example: `38 -> 3 + 8 = 11 -> 1 + 1 = 2`.",
        constraints=["0 <= n <= 10^18"],
        entry_point="digital_root", signature="def digital_root(n):",
        reference="def digital_root(n):\n    while n >= 10:\n        n = sum(int(c) for c in str(n))\n    return n\n",
        visible=[[38], [0], [7]],
        hidden=[[9], [10], [99], [999999999999999999], [123456789], [18], [1000000000000000000]],
        examples=["`38` becomes `11`, then `2`.", "A single digit is its own root."],
        complexity={"time": "O(log n)", "space": "O(1)"},
        approach="Loop while the number has two or more digits and replace it by its digit sum. (A formula with n % 9 also works, but check the multiples of 9 and zero.)",
    )
    problem(
        slug="caesar-cipher", title="Caesar Cipher", difficulty="easy", minutes=15, topics=["strings", "loops"], tags=["strings", "basics"], ds=["list", "loop", "condition"], roles=ALL,
        statement="Shift every English letter of `text` forward by `k` places in the alphabet, wrapping around from `z` to `a`. Keep the case of each letter and leave every other character unchanged. `k` may be negative or larger than 26.",
        constraints=["0 <= len(text) <= 100000", "-1000 <= k <= 1000", "Only the letters a-z and A-Z change"],
        entry_point="caesar", signature="def caesar(text, k):",
        reference="def caesar(text, k):\n    out = []\n    for ch in text:\n        if 'a' <= ch <= 'z':\n            out.append(chr((ord(ch) - 97 + k) % 26 + 97))\n        elif 'A' <= ch <= 'Z':\n            out.append(chr((ord(ch) - 65 + k) % 26 + 65))\n        else:\n            out.append(ch)\n    return ''.join(out)\n",
        visible=[["abc xyz", 3], ["Hello, World!", 5], ["", 4]],
        hidden=[["xyz", 3], ["ABC", -3], ["Zebra-123", 26], ["abc", 27], ["abc", -27], ["The quick brown fox", 13], ["a" * 1000, 1000]],
        examples=["`x`, `y`, `z` wrap to `a`, `b`, `c`.", "Punctuation and digits stay as they are."],
        complexity={"time": "O(n)", "space": "O(n)"},
        approach="Map each letter to 0 to 25, add k, take the result modulo 26 (Python handles negatives correctly) and map back, keeping the original case.",
    )
    problem(
        slug="move-zeros", title="Move Zeros to the End", difficulty="easy", minutes=10, topics=["arrays", "two pointers"], tags=["basics", "two-pointers"], ds=["list", "loop", "condition"], roles=ALL,
        statement="Return a new list in which all zeros of `nums` are moved to the end while the other numbers keep their original order.",
        constraints=["0 <= len(nums) <= 100000", "-10^9 <= nums[i] <= 10^9"],
        entry_point="move_zeros", signature="def move_zeros(nums):",
        reference="def move_zeros(nums):\n    out = [x for x in nums if x != 0]\n    return out + [0] * (len(nums) - len(out))\n",
        visible=[[[0, 1, 0, 3, 12]], [[0, 0]], [[]]],
        hidden=[[[1, 2, 3]], [[0]], [[0, 0, 1]], [[5, 0, 0, 4, 0, 3]], [[-1, 0, -2]], [[R.choice([0, 0, 1, -1, 7]) for _ in range(5000)]]],
        examples=["`[0, 1, 0, 3, 12]` becomes `[1, 3, 12, 0, 0]`.", "A list of zeros stays as it is."],
        complexity={"time": "O(n)", "space": "O(n)"},
        approach="Keep the non-zero values in order, then append as many zeros as were removed. A two-pointer version does it in place.",
    )
    # ---------------------------------------------------------------- MEDIUM
    problem(
        slug="min-stack-ops", title="Stack with Minimum", difficulty="medium", minutes=20, topics=["stacks"], tags=["stacks", "basics"], ds=["list", "tuple", "loop", "condition"], roles=ALL,
        statement="Simulate a stack that can report its minimum in O(1). `ops` is a list of operations: `[\"push\", x]`, `[\"pop\"]`, `[\"top\"]`, `[\"min\"]`. `pop` on an empty stack does nothing. For every `top` and `min` operation, add its result to the answer, or `None` when the stack is empty. Return the list of these results.",
        constraints=["0 <= len(ops) <= 50000", "-10^9 <= x <= 10^9", "Each operation must take O(1) time"],
        entry_point="min_stack_ops", signature="def min_stack_ops(ops):",
        reference="def min_stack_ops(ops):\n    stack = []\n    out = []\n    for op in ops:\n        if op[0] == 'push':\n            x = op[1]\n            stack.append((x, x if not stack else min(x, stack[-1][1])))\n        elif op[0] == 'pop':\n            if stack:\n                stack.pop()\n        elif op[0] == 'top':\n            out.append(stack[-1][0] if stack else None)\n        else:\n            out.append(stack[-1][1] if stack else None)\n    return out\n",
        visible=[[[["push", 3], ["push", 1], ["min"], ["pop"], ["min"], ["top"]]], [[["top"], ["min"]]], [[]]],
        hidden=[[[["push", 5], ["push", 5], ["pop"], ["min"]]], [[["push", 2], ["push", 0], ["push", 3], ["push", 0], ["pop"], ["min"], ["pop"], ["min"], ["pop"], ["min"]]], [[["pop"], ["push", 1], ["top"], ["pop"], ["pop"], ["min"]]], [[["push", -1], ["push", -2], ["min"], ["top"]]], [[["push", 1], ["push", 2], ["push", 3], ["pop"], ["pop"], ["min"], ["top"]]], [[["push", i % 100] if i % 3 else ["pop"] for i in range(3000)] + [["min"], ["top"]]]],
        examples=["After pushing 3 and 1 the minimum is 1; after a pop it is 3.", "On an empty stack `top` and `min` give `None`."],
        complexity={"time": "O(1) per operation", "space": "O(n)"},
        approach="Store with every pushed value the minimum of the stack at that moment, so after a pop the previous minimum is already known.",
    )
    problem(
        slug="linked-list-cycle", title="Cycle in a Linked List", difficulty="medium", minutes=20, topics=["linked lists", "two pointers"], tags=["linked-lists", "basics"], ds=["list", "loop", "condition"], roles=ALL,
        statement="A linked list is stored in an array: node `i` points to node `nxt[i]`, and `-1` means the end of the list. Starting at node `head` (`-1` for an empty list), return `True` if following the pointers ever visits a node twice, otherwise `False`. Nodes that cannot be reached from `head` do not matter.",
        constraints=["0 <= len(nxt) <= 100000", "-1 <= nxt[i] < len(nxt)", "head is -1 or a valid index", "Use O(1) extra memory if you can (Floyd's slow and fast pointers)"],
        entry_point="has_cycle", signature="def has_cycle(nxt, head):",
        reference="def has_cycle(nxt, head):\n    slow = fast = head\n    while fast != -1 and nxt[fast] != -1:\n        slow = nxt[slow]\n        fast = nxt[nxt[fast]]\n        if slow == fast:\n            return True\n    return False\n",
        visible=[[[1, 2, 3, 1], 0], [[1, 2, -1], 0], [[], -1]],
        hidden=[[[0], 0], [[-1], 0], [[1, 0], 0], [[1, 2, -1, 2], 3], [[1, 2, -1, 2], 0], [[1, 2, 3, 4, 2], 0], [[-1, 1], 1], [[i + 1 for i in range(9999)] + [-1], 0], [[i + 1 for i in range(9999)] + [5000], 0]],
        examples=["`0 -> 1 -> 2 -> 3 -> 1` repeats node 1, so the answer is `True`.", "The second list ends at node 2, so `False`."],
        complexity={"time": "O(n)", "space": "O(1)"},
        approach="Move a slow pointer one step and a fast pointer two steps. If the list has a cycle they meet; if the fast pointer reaches the end there is none.",
    )
    problem(
        slug="tree-level-order", title="Level Order of a Tree", difficulty="medium", minutes=20, topics=["trees", "queues"], tags=["trees", "recursion"], ds=["list", "loop"], roles=ALL,
        statement=TREE + "\n\nReturn the values of the tree level by level, from the top, and from left to right inside each level, as a list of lists. An empty tree gives `[]`.",
        constraints=["0 <= number of nodes <= 3000", "Tree depth <= 150", "-1000 <= value <= 1000"],
        entry_point="level_order", signature="def level_order(root):",
        reference="def level_order(root):\n    if not root:\n        return []\n    level = [root]\n    out = []\n    while level:\n        out.append([n[0] for n in level])\n        level = [c for n in level for c in (n[1], n[2]) if c]\n    return out\n",
        visible=[[[3, [9, None, None], [20, [15, None, None], [7, None, None]]]], [[1, None, None]], [None]],
        hidden=[[[1, [2, [4, None, None], None], [3, None, [5, None, None]]]], [chain(6)], [chain(6, 0)], [bst(range(1, 16))], [rand_tree(120)], [chain(150)]],
        examples=["The root is level 0, then 9 and 20, then 15 and 7.", "A single node gives `[[1]]`."],
        complexity={"time": "O(n)", "space": "O(n)"},
        approach="Process one whole level at a time with a list (or queue): record the level's values, then collect the children for the next level.",
    )
    problem(
        slug="validate-bst", title="Valid Binary Search Tree", difficulty="medium", minutes=25, topics=["trees", "recursion"], tags=["trees", "recursion"], ds=["list", "tuple", "loop", "condition"], roles=ALL,
        statement=TREE + "\n\nReturn `True` if the tree is a valid binary search tree: for every node, ALL values in its left subtree are smaller and ALL values in its right subtree are larger (equal values are not allowed). An empty tree is valid.",
        constraints=["0 <= number of nodes <= 3000", "Tree depth <= 150", "-10^9 <= value <= 10^9"],
        entry_point="is_valid_bst", signature="def is_valid_bst(root):",
        reference="def is_valid_bst(root):\n    stack = [(root, float('-inf'), float('inf'))]\n    while stack:\n        node, lo, hi = stack.pop()\n        if node is None:\n            continue\n        v = node[0]\n        if not lo < v < hi:\n            return False\n        stack.append((node[1], lo, v))\n        stack.append((node[2], v, hi))\n    return True\n",
        visible=[[[2, [1, None, None], [3, None, None]]], [[5, [1, None, None], [4, [3, None, None], [6, None, None]]]], [None]],
        hidden=[[[5, [4, None, None], [6, [3, None, None], [7, None, None]]]], [[2, [2, None, None], [3, None, None]]], [[1, None, [1, None, None]]], [bst(range(1, 40))], [[10, [5, None, [15, None, None]], [20, None, None]]], [chain(150)], [[0, [-1, None, None], None]], [rand_tree(60, 0, 100)]],
        examples=["The first tree is valid: 1 < 2 < 3.", "In the second tree the node 3 sits in the right subtree of 5 but is smaller than 5."],
        complexity={"time": "O(n)", "space": "O(h)"},
        approach="Carry the allowed range (lower and upper bound) down the tree. A node must be strictly inside its range, then its children get narrower ranges.",
    )
    problem(
        slug="tree-path-sum", title="Root-to-Leaf Path Sum", difficulty="medium", minutes=20, topics=["trees", "recursion"], tags=["trees", "recursion"], ds=["list", "loop", "condition"], roles=ALL,
        statement=TREE + "\n\nReturn `True` if there is a path from the root down to a LEAF (a node with no children) whose values add up to `target`. An empty tree has no path. Values can be negative.",
        constraints=["0 <= number of nodes <= 3000", "Tree depth <= 150", "-1000 <= value, target <= 10^6"],
        entry_point="has_path_sum", signature="def has_path_sum(root, target):",
        reference="def has_path_sum(root, target):\n    if root is None:\n        return False\n    stack = [(root, root[0])]\n    while stack:\n        node, total = stack.pop()\n        if node[1] is None and node[2] is None and total == target:\n            return True\n        for c in (node[1], node[2]):\n            if c is not None:\n                stack.append((c, total + c[0]))\n    return False\n",
        visible=[[[5, [4, [11, [7, None, None], [2, None, None]], None], [8, [13, None, None], [4, None, [1, None, None]]]], 22], [[1, [2, None, None], [3, None, None]], 5], [None, 5]],
        hidden=[[[1, [2, None, None], None], 1], [[1, [2, None, None], None], 3], [[-2, None, [-3, None, None]], -5], [[1, [2, None, None], [3, None, None]], 4], [[1, [2, None, None], [3, None, None]], 3], [chain(150), sum(range(1, 151))], [chain(150), 75], [[0, [1, None, None], [1, None, None]], 0], [None, 0]],
        examples=["The path 5 -> 4 -> 11 -> 2 adds up to 22.", "Sums that stop at a node that is not a leaf do not count."],
        complexity={"time": "O(n)", "space": "O(h)"},
        approach="Walk down while keeping the running sum. Only compare with the target when the node is a leaf.",
    )
    problem(
        slug="product-except-self", title="Product of the Others", difficulty="medium", minutes=20, topics=["arrays", "prefix sums"], tags=["basics", "grouping"], ds=["list", "loop"], roles=ALL,
        statement="Return a list `out` where `out[i]` is the product of all numbers of `nums` except `nums[i]`. Do it WITHOUT division, because `nums` may contain zeros.",
        constraints=["1 <= len(nums) <= 10000", "-30 <= nums[i] <= 30", "The answers fit in a normal Python integer"],
        entry_point="product_except_self", signature="def product_except_self(nums):",
        reference="def product_except_self(nums):\n    n = len(nums)\n    out = [1] * n\n    left = 1\n    for i in range(n):\n        out[i] = left\n        left *= nums[i]\n    right = 1\n    for i in range(n - 1, -1, -1):\n        out[i] *= right\n        right *= nums[i]\n    return out\n",
        visible=[[[1, 2, 3, 4]], [[-1, 1, 0, -3, 3]], [[5]]],
        hidden=[[[0, 0]], [[0, 4, 0]], [[1, 1, 1]], [[2, 3]], [[-2, -3, 4]], [[1, 0]], [[R.choice([1, 2, -1, 0, 3]) for _ in range(40)]]],
        examples=["For `[1, 2, 3, 4]` the answer is `[24, 12, 8, 6]`.", "With one zero, only the position of the zero is non-zero."],
        complexity={"time": "O(n)", "space": "O(1) extra"},
        approach="Multiply by the product of everything to the left in one pass, then by the product of everything to the right in a second pass.",
    )
    problem(
        slug="three-sum", title="Three Numbers that Sum to Zero", difficulty="medium", minutes=30, topics=["arrays", "two pointers", "sorting"], tags=["two-pointers", "sorting", "set-ops"], ds=["list", "tuple", "set", "loop", "condition"], roles=ALL,
        statement="Return all UNIQUE triplets `[a, b, c]` of values from `nums` (three different positions) with `a + b + c == 0`. Each triplet is sorted ascending and the list of triplets is sorted too. The same triplet of values must not appear twice.",
        constraints=["0 <= len(nums) <= 1500", "-10^5 <= nums[i] <= 10^5"],
        entry_point="three_sum", signature="def three_sum(nums):",
        reference="def three_sum(nums):\n    a = sorted(nums)\n    out = []\n    for i in range(len(a) - 2):\n        if i and a[i] == a[i - 1]:\n            continue\n        lo, hi = i + 1, len(a) - 1\n        while lo < hi:\n            s = a[i] + a[lo] + a[hi]\n            if s < 0:\n                lo += 1\n            elif s > 0:\n                hi -= 1\n            else:\n                out.append([a[i], a[lo], a[hi]])\n                lo += 1\n                while lo < hi and a[lo] == a[lo - 1]:\n                    lo += 1\n                hi -= 1\n    return out\n",
        visible=[[[-1, 0, 1, 2, -1, -4]], [[0, 1, 1]], [[0, 0, 0]]],
        hidden=[[[]], [[0, 0]], [[0, 0, 0, 0]], [[-2, 0, 1, 1, 2]], [[-4, -2, -2, -2, 0, 1, 2, 2, 2, 3, 3, 4, 4, 6, 6]], [[3, -1, -2, 5, -4, 1]], [[R.randint(-30, 30) for _ in range(200)]], [[R.randint(-400, 400) for _ in range(450)]]],
        examples=["`[-1, -1, 2]` and `[-1, 0, 1]` are the two unique triplets.", "No three numbers add up to zero in `[0, 1, 1]`."],
        complexity={"time": "O(n^2)", "space": "O(1) extra"},
        approach="Sort, fix the first number, then move two pointers inward from both ends. Skip equal values to avoid repeated triplets.",
    )
    problem(
        slug="daily-temperatures", title="Days Until Warmer", difficulty="medium", minutes=25, topics=["stacks", "arrays"], tags=["stacks", "simulation"], ds=["list", "tuple", "loop", "condition"], roles=ALL,
        statement="`temps[i]` is the temperature on day `i`. Return a list where entry `i` is the number of days you must wait after day `i` for a STRICTLY warmer temperature, or `0` if that never happens.",
        constraints=["0 <= len(temps) <= 30000", "-50 <= temps[i] <= 60", "A solution that scans forward from every day is too slow"],
        entry_point="daily_temperatures", signature="def daily_temperatures(temps):",
        reference="def daily_temperatures(temps):\n    out = [0] * len(temps)\n    stack = []\n    for i, t in enumerate(temps):\n        while stack and temps[stack[-1]] < t:\n            j = stack.pop()\n            out[j] = i - j\n        stack.append(i)\n    return out\n",
        visible=[[[73, 74, 75, 71, 69, 72, 76, 73]], [[30, 40, 50, 60]], [[]]],
        hidden=[[[30, 30, 30]], [[60, 50, 40]], [[50]], [[70, 70, 71]], [[1, 2, 1, 2, 1, 2]], [[R.randint(-10, 40) for _ in range(500)]], [list(range(14000, 0, -1))], [[-5] * 14000]],
        examples=["After 73 the next warmer day is the next one, so `1`.", "A temperature that is never exceeded gets `0`."],
        complexity={"time": "O(n)", "space": "O(n)"},
        approach="Keep a stack of days that are still waiting for a warmer day. When a warmer day arrives, pop every colder day and fill in the waiting time.",
    )
    problem(
        slug="subarray-sum-k", title="Subarrays with Sum K", difficulty="medium", minutes=25, topics=["arrays", "hash maps", "prefix sums"], tags=["hashing", "grouping"], ds=["list", "dict", "loop", "condition"], roles=ALL,
        statement="Count the continuous, non-empty subarrays of `nums` whose sum equals `k`. The numbers can be negative or zero.",
        constraints=["0 <= len(nums) <= 20000", "-1000 <= nums[i] <= 1000", "-10^6 <= k <= 10^6"],
        entry_point="subarray_sum", signature="def subarray_sum(nums, k):",
        reference="def subarray_sum(nums, k):\n    seen = {0: 1}\n    total = count = 0\n    for x in nums:\n        total += x\n        count += seen.get(total - k, 0)\n        seen[total] = seen.get(total, 0) + 1\n    return count\n",
        visible=[[[1, 1, 1], 2], [[1, 2, 3], 3], [[], 0]],
        hidden=[[[1, -1, 0], 0], [[0, 0, 0], 0], [[3, 4, 7, 2, -3, 1, 4, 2], 7], [[-1, -1, 1], 0], [[5], 5], [[5], 6], [[R.randint(-3, 3) for _ in range(300)], 3], [[R.randint(-5, 5) for _ in range(15000)], 4]],
        examples=["`[1, 1]` appears twice in `[1, 1, 1]`.", "Both `[1, 2]` and `[3]` add up to 3."],
        complexity={"time": "O(n)", "space": "O(n)"},
        approach="Keep a dictionary of how many times each prefix sum was seen. A subarray ending here sums to k for every earlier prefix equal to (current prefix - k).",
    )
    problem(
        slug="container-most-water", title="Container with Most Water", difficulty="medium", minutes=25, topics=["arrays", "two pointers"], tags=["two-pointers", "math-basics"], ds=["list", "loop", "condition"], roles=ALL,
        statement="`heights[i]` is the height of a vertical line at position `i`. Choose two lines; together with the x-axis they form a container whose water level is the shorter line. Return the largest area, which is (distance between the lines) times (the shorter height).",
        constraints=["0 <= len(heights) <= 20000", "0 <= heights[i] <= 10^4", "Fewer than two lines give 0"],
        entry_point="max_area", signature="def max_area(heights):",
        reference="def max_area(heights):\n    lo, hi = 0, len(heights) - 1\n    best = 0\n    while lo < hi:\n        best = max(best, (hi - lo) * min(heights[lo], heights[hi]))\n        if heights[lo] < heights[hi]:\n            lo += 1\n        else:\n            hi -= 1\n    return best\n",
        visible=[[[1, 8, 6, 2, 5, 4, 8, 3, 7]], [[1, 1]], [[]]],
        hidden=[[[5]], [[0, 0, 0]], [[4, 3, 2, 1, 4]], [[1, 2, 1]], [[2, 3, 4, 5, 18, 17, 6]], [[R.randint(0, 100) for _ in range(300)]], [[R.randint(0, 10000) for _ in range(15000)]]],
        examples=["Lines 1 and 8 (heights 8 and 7) are 7 apart: 7 x 7 = 49.", "Two lines of height 1 that are 1 apart give 1."],
        complexity={"time": "O(n)", "space": "O(1)"},
        approach="Start with the widest container and move the pointer at the shorter line inward, because only a taller line can improve the area.",
    )
    # ---------------------------------------------------------------- HARD
    problem(
        slug="tree-lca", title="Lowest Common Ancestor", difficulty="hard", minutes=30, topics=["trees", "recursion"], tags=["trees", "recursion"], ds=["list", "tuple", "loop", "condition"], roles=ALL,
        statement=TREE + "\n\nAll values are unique and both `p` and `q` exist in the tree. Return the value of the lowest common ancestor of the nodes with values `p` and `q`: the deepest node that has both of them in its subtree (a node counts as its own descendant). This is a general binary tree, NOT necessarily ordered.",
        constraints=["1 <= number of nodes <= 3000", "Tree depth <= 150", "Values are unique integers"],
        entry_point="lowest_common_ancestor", signature="def lowest_common_ancestor(root, p, q):",
        reference="def lowest_common_ancestor(root, p, q):\n    parent = {root[0]: None}\n    nodes = {root[0]: root}\n    stack = [root]\n    while stack:\n        n = stack.pop()\n        for c in (n[1], n[2]):\n            if c is not None:\n                parent[c[0]] = n[0]\n                nodes[c[0]] = c\n                stack.append(c)\n    ancestors = set()\n    x = p\n    while x is not None:\n        ancestors.add(x)\n        x = parent[x]\n    x = q\n    while x not in ancestors:\n        x = parent[x]\n    return x\n",
        visible=[[[3, [5, [6, None, None], [2, [7, None, None], [4, None, None]]], [1, [0, None, None], [8, None, None]]], 5, 1], [[3, [5, [6, None, None], [2, [7, None, None], [4, None, None]]], [1, [0, None, None], [8, None, None]]], 5, 4], [[1, [2, None, None], None], 1, 2]],
        hidden=[[[1, None, None], 1, 1], [[3, [5, [6, None, None], [2, [7, None, None], [4, None, None]]], [1, [0, None, None], [8, None, None]]], 6, 4], [[3, [5, [6, None, None], [2, [7, None, None], [4, None, None]]], [1, [0, None, None], [8, None, None]]], 7, 8], [[3, [5, [6, None, None], [2, [7, None, None], [4, None, None]]], [1, [0, None, None], [8, None, None]]], 3, 8], [chain(150), 75, 140], [chain(150, 0), 150, 50], [bst(range(1, 200)), 3, 190]],
        examples=["Nodes 5 and 1 only meet at the root 3.", "Node 5 is an ancestor of node 4, so the answer is 5."],
        complexity={"time": "O(n)", "space": "O(n)"},
        approach="Record each node's parent, collect all ancestors of p, then walk up from q until you hit one of them.",
    )
    problem(
        slug="trapping-rain-water", title="Trapping Rain Water", difficulty="hard", minutes=30, topics=["arrays", "two pointers"], tags=["two-pointers", "simulation", "math-basics"], ds=["list", "loop", "condition"], roles=ALL,
        statement="`heights[i]` is the height of a bar of width 1. After rain, water collects between the bars. Return the total units of trapped water.",
        constraints=["0 <= len(heights) <= 30000", "0 <= heights[i] <= 10^5"],
        entry_point="trap", signature="def trap(heights):",
        reference="def trap(heights):\n    lo, hi = 0, len(heights) - 1\n    left = right = water = 0\n    while lo < hi:\n        if heights[lo] < heights[hi]:\n            left = max(left, heights[lo])\n            water += left - heights[lo]\n            lo += 1\n        else:\n            right = max(right, heights[hi])\n            water += right - heights[hi]\n            hi -= 1\n    return water\n",
        visible=[[[0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]], [[4, 2, 0, 3, 2, 5]], [[]]],
        hidden=[[[1]], [[3, 0, 3]], [[1, 2, 3, 4]], [[4, 3, 2, 1]], [[5, 0, 0, 0, 5]], [[2, 0, 2, 0, 2]], [[R.randint(0, 50) for _ in range(500)]], [[R.randint(0, 100000) for _ in range(20000)]]],
        examples=["Between the bars of height 2 and 3 in the first example, water fills the gaps: 6 units in total.", "A rising or falling staircase holds nothing."],
        complexity={"time": "O(n)", "space": "O(1)"},
        approach="Water above a bar is limited by the lower of the highest bars on its left and right. Two pointers track both maxima while moving inward from the lower side.",
    )
    problem(
        slug="coin-change-min", title="Fewest Coins", difficulty="hard", minutes=30, topics=["dynamic programming"], tags=["dp", "math-basics", "fintech"], ds=["list", "loop", "condition"], roles=ALL,
        statement="Given the coin values `coins` (unlimited supply of each) and an `amount`, return the smallest number of coins that add up to exactly `amount`, or `-1` if it is impossible. An amount of 0 needs 0 coins.",
        constraints=["1 <= len(coins) <= 12", "1 <= coins[i] <= 10000", "0 <= amount <= 10000", "A greedy choice of the biggest coin is not always correct"],
        entry_point="coin_change", signature="def coin_change(coins, amount):",
        reference="def coin_change(coins, amount):\n    INF = amount + 1\n    best = [0] + [INF] * amount\n    for a in range(1, amount + 1):\n        for c in coins:\n            if c <= a and best[a - c] + 1 < best[a]:\n                best[a] = best[a - c] + 1\n    return best[amount] if best[amount] < INF else -1\n",
        visible=[[[1, 2, 5], 11], [[2], 3], [[1], 0]],
        hidden=[[[1, 3, 4], 6], [[2, 5, 10, 1], 27], [[5], 5], [[5], 7], [[186, 419, 83, 408], 6249], [[1, 5, 10, 25], 99], [[7, 3], 11], [[9999, 2], 10000], [[3, 7, 405, 436], 8839]],
        examples=["`11 = 5 + 5 + 1` needs 3 coins.", "3 cannot be made from 2s, so `-1`."],
        complexity={"time": "O(amount x coins)", "space": "O(amount)"},
        approach="best[a] is the fewest coins for amount a. For each a try every coin c and take best[a - c] + 1 when it is smaller.",
    )
    problem(
        slug="lis-length", title="Longest Increasing Subsequence", difficulty="hard", minutes=35, topics=["dynamic programming", "binary search"], tags=["dp", "searching", "sorting"], ds=["list", "loop", "condition"], roles=ALL,
        statement="Return the length of the longest STRICTLY increasing subsequence of `nums` (items taken in order, not necessarily next to each other).",
        constraints=["0 <= len(nums) <= 20000", "-10^9 <= nums[i] <= 10^9", "O(n log n) is possible and needed for the largest inputs"],
        entry_point="length_of_lis", signature="def length_of_lis(nums):",
        reference="import bisect\n\n\ndef length_of_lis(nums):\n    tails = []\n    for x in nums:\n        i = bisect.bisect_left(tails, x)\n        if i == len(tails):\n            tails.append(x)\n        else:\n            tails[i] = x\n    return len(tails)\n",
        visible=[[[10, 9, 2, 5, 3, 7, 101, 18]], [[0, 1, 0, 3, 2, 3]], [[]]],
        hidden=[[[7, 7, 7, 7]], [[5]], [[1, 2, 3, 4, 5]], [[5, 4, 3, 2, 1]], [[1, 3, 2, 4, 3, 5]], [[4, 10, 4, 3, 8, 9]], [[R.randint(-1000, 1000) for _ in range(500)]], [list(range(15000))], [[R.randint(-10**9, 10**9) for _ in range(15000)]]],
        examples=["`2, 3, 7, 101` has length 4.", "Equal numbers do not count as increasing."],
        complexity={"time": "O(n log n)", "space": "O(n)"},
        approach="Keep tails[k], the smallest possible last value of an increasing subsequence of length k+1. For each number, binary search its place in tails and replace or append.",
    )
    problem(
        slug="word-ladder-length", title="Word Ladder", difficulty="hard", minutes=40, topics=["graphs", "breadth-first search"], tags=["graphs", "simulation", "strings"], ds=["list", "set", "dict", "loop", "condition"], roles=ALL,
        statement="Change `begin` into `end` one letter at a time. Every intermediate word must be in `words`, and `end` itself must be in `words` too. Return the number of words in the shortest sequence, counting both `begin` and `end`, or `0` if there is no such sequence. All words are lowercase and have the same length.",
        constraints=["0 <= len(words) <= 2000", "1 <= len(word) <= 10", "begin is not necessarily in words"],
        entry_point="ladder_length", signature="def ladder_length(begin, end, words):",
        reference="from collections import deque\n\n\ndef ladder_length(begin, end, words):\n    pool = set(words)\n    if end not in pool:\n        return 0\n    q = deque([(begin, 1)])\n    seen = {begin}\n    while q:\n        w, d = q.popleft()\n        if w == end:\n            return d\n        for i in range(len(w)):\n            for c in 'abcdefghijklmnopqrstuvwxyz':\n                n = w[:i] + c + w[i + 1:]\n                if n in pool and n not in seen:\n                    seen.add(n)\n                    q.append((n, d + 1))\n    return 0\n",
        visible=[["hit", "cog", ["hot", "dot", "dog", "lot", "log", "cog"]], ["hit", "cog", ["hot", "dot", "dog", "lot", "log"]], ["a", "c", ["a", "b", "c"]]],
        hidden=[["hit", "hit", ["hit"]], ["hit", "hot", ["hot"]], ["hit", "dog", ["hot", "dot", "dog"]], ["red", "tax", ["ted", "tex", "red", "tax", "tad", "den", "rex", "pee"]], ["lost", "cost", ["most", "fist", "lost", "cost", "fish"]], ["aaaa", "zzzz", []], ["abc", "abd", ["abd"]], ["hot", "dog", ["hot", "dog"]], ["hit", "hot", ["hit"]], ["hit", "cog", ["hot", "dot"]]],
        examples=["`hit -> hot -> dot -> dog -> cog` has 5 words.", "Without `cog` in the list, the answer is 0."],
        complexity={"time": "O(N x L x 26)", "space": "O(N)"},
        approach="Breadth-first search on words: from each word try changing each letter to every other letter and move to words that are in the list and not yet seen. The first time you reach `end` is the shortest.",
    )
    problem(
        slug="merge-k-sorted", title="Merge K Sorted Lists", difficulty="hard", minutes=30, topics=["heaps", "sorting"], tags=["sorting", "two-pointers"], ds=["list", "tuple", "loop", "condition"], roles=ALL,
        statement="`lists` is a list of lists, each already sorted ascending. Merge them into ONE sorted list that keeps duplicates. Some lists can be empty.",
        constraints=["0 <= len(lists) <= 500", "Total number of items <= 20000", "-10^9 <= value <= 10^9", "Sorting the concatenation works but a heap is the expected approach"],
        entry_point="merge_k_lists", signature="def merge_k_lists(lists):",
        reference="import heapq\n\n\ndef merge_k_lists(lists):\n    heap = [(l[0], i, 0) for i, l in enumerate(lists) if l]\n    heapq.heapify(heap)\n    out = []\n    while heap:\n        v, i, j = heapq.heappop(heap)\n        out.append(v)\n        if j + 1 < len(lists[i]):\n            heapq.heappush(heap, (lists[i][j + 1], i, j + 1))\n    return out\n",
        visible=[[[[1, 4, 5], [1, 3, 4], [2, 6]]], [[]], [[[], []]]],
        hidden=[[[[1]]], [[[2], [1]]], [[[1, 1], [1, 1]]], [[[], [5, 6], []]], [[[-3, -1], [-2, 0]]], [[sorted(R.randint(-100, 100) for _ in range(20)) for _ in range(30)]], [[sorted(R.randint(-10**9, 10**9) for _ in range(40)) for _ in range(150)]]],
        examples=["The three lists merge into `[1, 1, 2, 3, 4, 4, 5, 6]`.", "Empty input lists give `[]`."],
        complexity={"time": "O(N log k)", "space": "O(k)"},
        approach="Keep a min-heap with the current head of every list. Pop the smallest, add it to the answer and push the next item of the same list.",
    )
    problem(
        slug="edit-distance", title="Edit Distance", difficulty="hard", minutes=35, topics=["dynamic programming", "strings"], tags=["dp", "strings"], ds=["list", "loop", "condition"], roles=ALL,
        statement="Return the minimum number of single-character operations (insert, delete or replace a character) needed to turn the string `a` into the string `b`.",
        constraints=["0 <= len(a), len(b) <= 500", "Lowercase letters only"],
        entry_point="edit_distance", signature="def edit_distance(a, b):",
        reference="def edit_distance(a, b):\n    prev = list(range(len(b) + 1))\n    for i in range(1, len(a) + 1):\n        cur = [i] + [0] * len(b)\n        for j in range(1, len(b) + 1):\n            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] != b[j - 1]))\n        prev = cur\n    return prev[-1]\n",
        visible=[["horse", "ros"], ["intention", "execution"], ["", "abc"]],
        hidden=[["", ""], ["abc", "abc"], ["abc", ""], ["a", "b"], ["kitten", "sitting"], ["sunday", "saturday"], ["abcdef", "azced"], ["".join(R.choice("abc") for _ in range(300)), "".join(R.choice("abc") for _ in range(300))]],
        examples=["`horse` to `ros` takes 3 operations.", "Turning an empty string into `abc` needs 3 inserts."],
        complexity={"time": "O(len(a) x len(b))", "space": "O(len(b))"},
        approach="dp[i][j] is the distance between the first i letters of a and the first j of b. Take the cheapest of delete, insert and replace (free when the letters match).",
    )
    problem(
        slug="n-queens-count", title="Count N-Queens", difficulty="hard", minutes=40, topics=["backtracking", "recursion"], tags=["backtracking", "recursion", "simulation"], ds=["list", "set", "loop", "condition"], roles=ALL,
        statement="Place `n` queens on an `n x n` chessboard so that no two attack each other (no shared row, column or diagonal). Return the number of different valid placements.",
        constraints=["1 <= n <= 9"],
        entry_point="count_queens", signature="def count_queens(n):",
        reference="def count_queens(n):\n    cols, d1, d2 = set(), set(), set()\n    def place(r):\n        if r == n:\n            return 1\n        total = 0\n        for c in range(n):\n            if c in cols or r - c in d1 or r + c in d2:\n                continue\n            cols.add(c)\n            d1.add(r - c)\n            d2.add(r + c)\n            total += place(r + 1)\n            cols.remove(c)\n            d1.remove(r - c)\n            d2.remove(r + c)\n        return total\n    return place(0)\n",
        visible=[[4], [1], [2]],
        hidden=[[3], [5], [6], [7], [8], [9]],
        examples=["4 queens have 2 solutions.", "2 and 3 queens have none."],
        complexity={"time": "about O(n!)", "space": "O(n)"},
        approach="Place one queen per row with backtracking. Keep sets of used columns and both diagonals (row - col and row + col) so each check is O(1).",
    )
    problem(
        slug="longest-valid-parentheses", title="Longest Valid Parentheses", difficulty="hard", minutes=35, topics=["stacks", "strings", "dynamic programming"], tags=["stacks", "strings", "dp"], ds=["list", "loop", "condition"], roles=ALL,
        statement="`s` contains only `(` and `)`. Return the length of the longest CONTIGUOUS substring that is a valid, balanced set of parentheses.",
        constraints=["0 <= len(s) <= 30000"],
        entry_point="longest_valid", signature="def longest_valid(s):",
        reference="def longest_valid(s):\n    stack = [-1]\n    best = 0\n    for i, ch in enumerate(s):\n        if ch == '(':\n            stack.append(i)\n        else:\n            stack.pop()\n            if stack:\n                best = max(best, i - stack[-1])\n            else:\n                stack.append(i)\n    return best\n",
        visible=[["(()"], [")()())"], [""]],
        hidden=[["()"], ["((("], [")))"], ["()(()"], ["()(())"], ["(()())"], ["(()("], ["(()()"], ["((()))("], ["(()(()"], ["())(())"], ["".join(R.choice("()") for _ in range(400))], ["()" * 10000], ["(" * 5000 + ")" * 5000]],
        examples=["In `(()` the longest valid part is `()`, length 2.", "In `)()())` it is `()()`, length 4."],
        complexity={"time": "O(n)", "space": "O(n)"},
        approach="Keep a stack of indexes with the index of the last unmatched position at the bottom. When a pair closes, the valid length is the distance to the new top of the stack.",
    )
    problem(
        slug="sliding-window-max", title="Sliding Window Maximum", difficulty="hard", minutes=35, topics=["queues", "arrays"], tags=["two-pointers", "simulation", "sorting"], ds=["list", "loop", "condition"], roles=ALL,
        statement="For every window of `k` consecutive numbers of `nums`, moving from left to right, return the maximum of the window. The answer has `len(nums) - k + 1` values.",
        constraints=["1 <= k <= len(nums) <= 30000", "-10^9 <= nums[i] <= 10^9", "Scanning each window fully is too slow for the largest inputs"],
        entry_point="max_sliding_window", signature="def max_sliding_window(nums, k):",
        reference="from collections import deque\n\n\ndef max_sliding_window(nums, k):\n    dq = deque()\n    out = []\n    for i, x in enumerate(nums):\n        while dq and nums[dq[-1]] <= x:\n            dq.pop()\n        dq.append(i)\n        if dq[0] <= i - k:\n            dq.popleft()\n        if i >= k - 1:\n            out.append(nums[dq[0]])\n    return out\n",
        visible=[[[1, 3, -1, -3, 5, 3, 6, 7], 3], [[1], 1], [[9, 11], 2]],
        hidden=[[[4, 3, 2, 1], 2], [[1, 2, 3, 4], 2], [[5, 5, 5], 2], [[-7, -8, 7, 5, 7, 1, 6, 0], 4], [[1, -1], 1], [[R.randint(-50, 50) for _ in range(300)], 7], [[R.randint(-10**9, 10**9) for _ in range(6000)], 1500], [list(range(6000, 0, -1)), 3000]],
        examples=["The windows of 3 have maximums 3, 3, 5, 5, 6, 7.", "With `k = 1` the answer is the list itself."],
        complexity={"time": "O(n)", "space": "O(k)"},
        approach="Keep a deque of indexes whose values decrease. Drop smaller values from the back when a new number arrives and drop the front when it leaves the window; the front is the maximum.",
    )
