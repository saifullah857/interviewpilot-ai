"""More screening-style problems (see problems_screening_a.py for the conventions)."""
import random

from problems_screening_a import ALL, BACK, DATA, SW

R = random.Random(23)


def define(problem):
    problem(
        slug="inventory-restock", title="Inventory Restock", difficulty="easy", minutes=15, topics=["dictionaries", "lists", "conditions", "loops"], tags=["business-rules", "grouping"], ds=["dict", "list", "tuple", "loop", "condition"], roles=ALL,
        statement="`stock` is a dictionary item -> quantity in stock, and `minimum` is a dictionary item -> minimum quantity that must be kept. For every item in `minimum` that is below its minimum (an item missing from `stock` counts as 0), the shop must order the difference.\n\nReturn a list of `[item, quantity_to_order]` sorted by item name. Items that already have enough stock are left out.",
        constraints=["0 <= number of items <= 5000", "All quantities are non-negative integers", "Items in `stock` that are not in `minimum` are ignored"],
        entry_point="inventory_restock", signature="def inventory_restock(stock, minimum):",
        reference="def inventory_restock(stock, minimum):\n    out = []\n    for item in sorted(minimum):\n        have = stock.get(item, 0)\n        if have < minimum[item]:\n            out.append([item, minimum[item] - have])\n    return out\n",
        visible=[[{"pen": 3, "ink": 10}, {"pen": 5, "ink": 10}], [{}, {"a": 2}], [{"a": 1}, {}]],
        hidden=[[{}, {}], [{"a": 5}, {"a": 5}], [{"a": 4, "b": 0}, {"a": 5, "b": 1, "c": 3}], [{"x": 9, "extra": 1}, {"x": 10}], [{"a": 0}, {"a": 1, "b": 0}], [{f"i{k}": k % 9 for k in range(2000)}, {f"i{k}": 4 for k in range(2000)}]],
        examples=["Only `pen` is below its minimum, by 2.", "A missing item counts as 0 in stock."],
        complexity={"time": "O(n log n)", "space": "O(n)"},
        approach="Loop over the sorted minimum dictionary, read the stock with `dict.get(item, 0)` and add the shortfall when stock is lower.",
    )
    problem(
        slug="primes-upto", title="Primes up to N", difficulty="easy", minutes=15, topics=["loops", "lists", "math", "conditions"], tags=["math-basics", "basics"], ds=["list", "loop", "condition"], roles=ALL,
        statement="Return the list of all prime numbers less than or equal to `n`, in ascending order. A prime is a number greater than 1 with no divisors other than 1 and itself. The sieve of Eratosthenes keeps this fast for large `n`.",
        constraints=["0 <= n <= 200000", "n = 0 or 1 gives an empty list"],
        entry_point="primes_upto", signature="def primes_upto(n):",
        reference="def primes_upto(n):\n    if n < 2:\n        return []\n    sieve = [True] * (n + 1)\n    sieve[0] = sieve[1] = False\n    for i in range(2, int(n ** 0.5) + 1):\n        if sieve[i]:\n            for j in range(i * i, n + 1, i):\n                sieve[j] = False\n    return [i for i, ok in enumerate(sieve) if ok]\n",
        visible=[[10], [1], [2]],
        hidden=[[0], [3], [4], [29], [30], [100], [97], [50000]],
        examples=["`2, 3, 5, 7` are the primes up to 10.", "There are no primes up to 1."],
        complexity={"time": "O(n log log n)", "space": "O(n)"},
        approach="Make a list of booleans; for each prime i mark its multiples from i*i as not prime. The numbers still marked True are the primes.",
    )
    problem(
        slug="run-length-encode", title="Run-Length Encoding", difficulty="easy", minutes=10, topics=["strings", "loops", "conditions"], tags=["strings", "basics"], ds=["list", "tuple", "loop", "condition"], roles=ALL,
        statement="Compress a string by replacing each run of the same character with the character followed by the run length, but write nothing for a run of length 1. Example: `\"aaabccdd\"` becomes `\"a3bc2d2\"`.\n\nReturn the compressed string. A run of length 1 stays as the single character.",
        constraints=["0 <= len(s) <= 100000", "s has no digits", "The empty string gives the empty string"],
        entry_point="rle", signature="def rle(s):",
        reference="def rle(s):\n    out = []\n    i = 0\n    while i < len(s):\n        j = i\n        while j < len(s) and s[j] == s[i]:\n            j += 1\n        out.append(s[i] + (str(j - i) if j - i > 1 else ''))\n        i = j\n    return ''.join(out)\n",
        visible=[["aaabccdd"], ["abc"], [""]],
        hidden=[["a"], ["aa"], ["aabbaa"], ["zzzzzzzzzzzz"], ["abababab"], ["x" * 10000], ["ab" * 5000]],
        examples=["`aaa` -> `a3`, `b` stays `b`, `cc` -> `c2`, `dd` -> `d2`.", "No repeats means the string is unchanged."],
        complexity={"time": "O(n)", "space": "O(n)"},
        approach="Walk with two indexes: find the end of the current run, append the character and the count (only when the count is above 1).",
    )
    problem(
        slug="roman-to-int", title="Roman Numeral to Integer", difficulty="easy", minutes=15, topics=["dictionaries", "strings", "loops", "conditions"], tags=["strings", "math-basics"], ds=["dict", "loop", "condition"], roles=ALL,
        statement="Convert a Roman numeral to an integer. Symbols: `I=1, V=5, X=10, L=50, C=100, D=500, M=1000`. When a smaller symbol comes BEFORE a larger one it is subtracted (`IV = 4`, `IX = 9`, `XL = 40`, `XC = 90`, `CD = 400`, `CM = 900`), otherwise it is added. The input is always a valid numeral from 1 to 3999.",
        constraints=["1 <= value <= 3999", "Input uses only the seven uppercase symbols"],
        entry_point="roman_to_int", signature="def roman_to_int(s):",
        reference="def roman_to_int(s):\n    values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}\n    total = 0\n    for i, ch in enumerate(s):\n        v = values[ch]\n        if i + 1 < len(s) and v < values[s[i + 1]]:\n            total -= v\n        else:\n            total += v\n    return total\n",
        visible=[["III"], ["LVIII"], ["MCMXCIV"]],
        hidden=[["I"], ["IV"], ["IX"], ["XL"], ["XC"], ["CD"], ["CM"], ["MMMCMXCIX"], ["MDCLXVI"]],
        examples=["`MCMXCIV` = 1000 + (1000 - 100) + (100 - 10) + (5 - 1) = 1994.", "`III` = 3."],
        complexity={"time": "O(n)", "space": "O(1)"},
        approach="Use a dict of symbol values. Look one symbol ahead: if the next symbol is larger, subtract the current value, otherwise add it.",
    )
    problem(
        slug="palindrome-filter", title="Filter Palindromes", difficulty="easy", minutes=15, topics=["strings", "lists", "sets", "conditions"], tags=["strings", "basics", "set-ops"], ds=["list", "set", "loop", "condition"], roles=ALL,
        statement="From a list of phrases, return the phrases that are palindromes when you ignore case and ignore everything that is not a letter or digit (letters a-z, A-Z, digits 0-9). An empty cleaned phrase does NOT count. Keep the original phrase text and the original order, and keep a phrase only the first time it appears (exact same text).",
        constraints=["0 <= len(phrases) <= 20000", "Each phrase has at most 200 characters", "Compare phrases for duplicates exactly as written"],
        entry_point="palindrome_filter", signature="def palindrome_filter(phrases):",
        reference="def palindrome_filter(phrases):\n    seen = set()\n    out = []\n    for p in phrases:\n        if p in seen:\n            continue\n        clean = [c.lower() for c in p if c.isascii() and c.isalnum()]\n        if clean and clean == clean[::-1]:\n            seen.add(p)\n            out.append(p)\n    return out\n",
        visible=[[["Racecar", "hello", "A man, a plan, a canal: Panama"]], [["!!!", ""]], [["abba", "abba"]]],
        hidden=[[[]], [["12321", "123"]], [["No lemon, no melon", "Was it a car?"]], [["Aa", "aA", "Aa"]], [["x"]], [["ab" * 50 + "ba" * 50] * 100]],
        examples=["`Racecar` and the Panama phrase read the same both ways.", "Punctuation-only text is ignored and does not count."],
        complexity={"time": "O(n * L)", "space": "O(n)"},
        approach="Clean each phrase into a list of lowercase alphanumeric characters, compare with its reverse, and use a set to drop repeated phrases.",
    )
    problem(
        slug="moving-average", title="Moving Average", difficulty="easy", minutes=15, topics=["lists", "loops", "math"], tags=["math-basics", "data-cleaning"], ds=["list", "loop", "condition"], roles=DATA + SW,
        statement="Given a list of numbers `values` and a window size `k`, return the list of averages of every `k` consecutive values, each rounded to 2 decimals with `round()`. The answer has `len(values) - k + 1` numbers. If `k` is larger than the list, return an empty list.",
        constraints=["0 <= len(values) <= 50000", "1 <= k <= 100000", "Values are integers or floats"],
        entry_point="moving_average", signature="def moving_average(values, k):",
        reference="def moving_average(values, k):\n    if k > len(values):\n        return []\n    window = sum(values[:k])\n    out = [round(window / k, 2)]\n    for i in range(k, len(values)):\n        window += values[i] - values[i - k]\n        out.append(round(window / k, 2))\n    return out\n",
        visible=[[[1, 2, 3, 4, 5], 3], [[10], 1], [[1, 2], 5]],
        hidden=[[[], 1], [[5, 5, 5, 5], 2], [[1, 2, 4], 2], [[-1, 1, -1, 1], 2], [[0.5, 1.5, 2.5], 3], [[i % 97 for i in range(5000)], 7]],
        examples=["`(1+2+3)/3 = 2.0`, `(2+3+4)/3 = 3.0`, `(3+4+5)/3 = 4.0`.", "A window larger than the list gives `[]`."],
        complexity={"time": "O(n)", "space": "O(n)"},
        approach="Keep a running window sum: add the new value and remove the one that left. This is O(n) instead of re-adding k values each time.",
        tolerance=1e-9,
    )
    problem(
        slug="cart-by-category", title="Shopping Cart by Category", difficulty="medium", minutes=20, topics=["dictionaries", "lists", "sorting", "loops"], tags=["grouping", "business-rules"], ds=["list", "tuple", "dict", "set", "loop"], roles=SW + ["data-scientist"],
        statement="`cart` is a list of `[product, category, price, quantity]`. Group by category and return a list of `[category, total, products]` where `total` is the sum of price * quantity (an integer; prices are whole numbers) and `products` is the sorted list of DISTINCT product names in that category.\n\nSort the result by total (highest first), then by category name.",
        constraints=["0 <= len(cart) <= 20000", "price >= 0 and quantity >= 0 are integers", "The same product can appear on several lines"],
        entry_point="cart_by_category", signature="def cart_by_category(cart):",
        reference="def cart_by_category(cart):\n    totals = {}\n    names = {}\n    for product, cat, price, qty in cart:\n        totals[cat] = totals.get(cat, 0) + price * qty\n        names.setdefault(cat, set()).add(product)\n    rows = [[c, totals[c], sorted(names[c])] for c in totals]\n    rows.sort(key=lambda r: (-r[1], r[0]))\n    return rows\n",
        visible=[[[["tv", "elec", 300, 1], ["fan", "elec", 50, 2], ["rice", "food", 20, 5]]], [[]], [[["a", "x", 1, 1], ["a", "x", 1, 1]]]],
        hidden=[[[["a", "b", 0, 5]]], [[["a", "c1", 10, 1], ["b", "c2", 10, 1]]], [[["z", "k", 5, 2], ["y", "k", 5, 2], ["z", "k", 1, 1]]], [[["p", "m", 100, 3], ["q", "n", 300, 1]]], [[["p", "z", 2, 2]]], [[[f"p{i % 300}", f"c{i % 25}", i % 90, (i % 4) + 1] for i in range(3000)]]],
        examples=["`elec` totals 400 and `food` totals 100; `elec` comes first.", "Duplicate product names appear once in the list but both lines count in the total."],
        complexity={"time": "O(n log n)", "space": "O(n)"},
        approach="Use one dict for totals and one dict of sets for distinct products, then sort the rows by (-total, category).",
    )
    problem(
        slug="matrix-spiral", title="Spiral Order of a Matrix", difficulty="medium", minutes=25, topics=["lists", "loops", "conditions"], tags=["matrix", "simulation"], ds=["list", "tuple", "loop", "condition"], roles=ALL,
        statement="Given a rectangular matrix (list of equal-length rows), return all its elements in spiral order: left to right along the top row, down the right column, right to left along the bottom row, up the left column, then continue inward.",
        constraints=["0 <= rows, columns <= 200", "All rows have the same length", "An empty matrix gives `[]`"],
        entry_point="spiral_order", signature="def spiral_order(matrix):",
        reference="def spiral_order(matrix):\n    out = []\n    if not matrix or not matrix[0]:\n        return out\n    top, bottom, left, right = 0, len(matrix) - 1, 0, len(matrix[0]) - 1\n    while top <= bottom and left <= right:\n        for c in range(left, right + 1):\n            out.append(matrix[top][c])\n        for r in range(top + 1, bottom + 1):\n            out.append(matrix[r][right])\n        if top < bottom and left < right:\n            for c in range(right - 1, left - 1, -1):\n                out.append(matrix[bottom][c])\n            for r in range(bottom - 1, top, -1):\n                out.append(matrix[r][left])\n        top, bottom, left, right = top + 1, bottom - 1, left + 1, right - 1\n    return out\n",
        visible=[[[[1, 2, 3], [4, 5, 6], [7, 8, 9]]], [[[1, 2, 3, 4]]], [[]]],
        hidden=[[[[1]]], [[[1], [2], [3]]], [[[1, 2], [3, 4]]], [[[1, 2, 3], [4, 5, 6]]], [[[1, 2], [3, 4], [5, 6]]], [[[r * 200 + c for c in range(60)] for r in range(60)]], [[[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]]],
        examples=["`[[1,2,3],[4,5,6],[7,8,9]]` gives `[1, 2, 3, 6, 9, 8, 7, 4, 5]`.", "A single row is read left to right."],
        complexity={"time": "O(r * c)", "space": "O(r * c)"},
        approach="Track four boundaries (top, bottom, left, right) and walk the edges, shrinking the boundaries after each lap. Guard the last two edges so a single remaining row or column is not read twice.",
    )
    problem(
        slug="first-unique-char", title="First Non-Repeating Character", difficulty="easy", minutes=10, topics=["dictionaries", "strings", "loops"], tags=["strings", "hashing", "basics"], ds=["dict", "loop", "condition"], roles=ALL,
        statement="Return the INDEX of the first character in `s` that appears exactly once in the whole string, or `-1` if there is none.",
        constraints=["0 <= len(s) <= 100000", "s may contain any printable ASCII characters"],
        entry_point="first_unique", signature="def first_unique(s):",
        reference="def first_unique(s):\n    counts = {}\n    for ch in s:\n        counts[ch] = counts.get(ch, 0) + 1\n    for i, ch in enumerate(s):\n        if counts[ch] == 1:\n            return i\n    return -1\n",
        visible=[["leetcode"], ["aabb"], [""]],
        hidden=[["a"], ["aab"], ["abab c"], ["loveleetcode"], ["xxyyzzw"], ["ab" * 5000 + "c"], ["a" * 10000]],
        examples=["`l` appears once and is at index 0.", "Every character repeats, so the answer is `-1`."],
        complexity={"time": "O(n)", "space": "O(k)"},
        approach="Count every character with a dict, then scan the string again and return the first index whose count is 1.",
    )
