"""Screening-style problems that combine list, tuple, dict, set, loops and conditions, the way software-house screening rounds usually do.
Imported by build_coding_problems.py. `tags` are focus tags used to match a software house's focus profile and the resume's skills;
`ds` lists the Python structures the problem makes you combine. Expected outputs are computed from `reference` at build time."""
import random

R = random.Random(11)
ALL = ["python-developer", "backend-developer", "full-stack-developer", "frontend-developer", "mobile-app-developer", "ai-ml-engineer-intern", "junior-ai-engineer", "data-scientist"]
SW = ["python-developer", "backend-developer", "full-stack-developer", "frontend-developer", "mobile-app-developer"]
DATA = ["python-developer", "ai-ml-engineer-intern", "junior-ai-engineer", "data-scientist", "backend-developer"]
BACK = ["python-developer", "backend-developer", "full-stack-developer"]


def define(problem):
    # ---------------------------------------------------------------- 1
    problem(
        slug="unique-keep-order", title="Remove Duplicates, Keep Order", difficulty="easy", minutes=10, topics=["lists", "sets", "loops"], tags=["basics", "set-ops"], ds=["list", "set", "loop", "condition"], roles=ALL,
        statement="Given a list `items` of integers, return a new list that contains each value only once, keeping the order of its FIRST appearance.\n\nExample idea: a set remembers what you have already seen while a loop builds the answer.",
        constraints=["0 <= len(items) <= 100000", "-10^9 <= items[i] <= 10^9", "Return a new list; do not sort"],
        entry_point="unique_keep_order", signature="def unique_keep_order(items):",
        reference="def unique_keep_order(items):\n    seen = set()\n    out = []\n    for x in items:\n        if x not in seen:\n            seen.add(x)\n            out.append(x)\n    return out\n",
        visible=[[[3, 1, 3, 2, 1]], [[5, 5, 5]], [[]]],
        hidden=[[[1, 2, 3]], [[-1, -1, 0, 0, 1]], [[9, 8, 9, 8, 7]], [[0]], [[2, 1, 2, 1, 2, 1]], [[i % 1000 for i in range(10000)]], [[R.randint(-50, 50) for _ in range(5000)]]],
        examples=["`3` and `1` repeat, so only their first appearance is kept: `[3, 1, 2]`.", "All values are `5`, so one `5` remains."],
        complexity={"time": "O(n)", "space": "O(n)"},
        approach="Loop once. A set gives O(1) 'have I seen this?' checks; append to the result only when the value is new.",
    )
    # ---------------------------------------------------------------- 2
    problem(
        slug="common-elements", title="Common Elements of Two Lists", difficulty="easy", minutes=10, topics=["sets", "lists", "sorting"], tags=["basics", "set-ops"], ds=["list", "set", "condition"], roles=ALL,
        statement="Given two lists of integers `a` and `b`, return a sorted list of the values that appear in BOTH lists. Each common value appears once in the answer, even if it repeats in the inputs.",
        constraints=["0 <= len(a), len(b) <= 50000", "-10^6 <= value <= 10^6", "Return the values in ascending order"],
        entry_point="common_elements", signature="def common_elements(a, b):",
        reference="def common_elements(a, b):\n    return sorted(set(a) & set(b))\n",
        visible=[[[1, 2, 2, 3], [2, 3, 4]], [[5, 6], [7, 8]], [[], [1]]],
        hidden=[[[1, 1, 1], [1]], [[-3, -2, -1], [-1, -2, 5]], [[0], [0, 0]], [[1, 2, 3, 4], [4, 3, 2, 1]], [[10, 20], []], [list(range(0, 10000, 2)), list(range(0, 10000, 3))]],
        examples=["`2` and `3` are in both lists, so `[2, 3]`.", "Nothing is shared, so the answer is `[]`."],
        complexity={"time": "O(n log n)", "space": "O(n)"},
        approach="Turn both lists into sets and intersect them; sort the result.",
    )
    # ---------------------------------------------------------------- 3
    problem(
        slug="grade-report", title="Student Grade Report", difficulty="easy", minutes=15, topics=["dictionaries", "conditions", "loops", "sorting"], tags=["business-rules", "grouping"], ds=["dict", "list", "loop", "condition"], roles=ALL,
        statement="`marks` is a dictionary that maps a student name to a list of that student's marks (0 to 100). For each student compute the average (rounded to 2 decimals with `round()`) and a grade: `A` for average >= 85, `B` for >= 70, `C` for >= 50, otherwise `F`. A student with an empty list has average `0.0` and grade `F`.\n\nReturn a list of `[name, average, grade]`, sorted by average (highest first), then by name alphabetically.",
        constraints=["0 <= number of students <= 2000", "0 <= each mark <= 100", "Names are unique"],
        entry_point="grade_report", signature="def grade_report(marks):",
        reference="def grade_report(marks):\n    rows = []\n    for name, ms in marks.items():\n        avg = round(sum(ms) / len(ms), 2) if ms else 0.0\n        if avg >= 85:\n            g = 'A'\n        elif avg >= 70:\n            g = 'B'\n        elif avg >= 50:\n            g = 'C'\n        else:\n            g = 'F'\n        rows.append([name, avg, g])\n    rows.sort(key=lambda r: (-r[1], r[0]))\n    return rows\n",
        visible=[[{"Ali": [90, 80], "Sara": [60, 70, 65]}], [{"Zed": []}], [{"A": [85], "B": [84, 85]}]],
        hidden=[[{}], [{"Bilal": [50, 50], "Ayesha": [50]}], [{"x": [100, 100, 100], "y": [70, 70], "z": [49, 50]}], [{"q": [69, 70]}], [{"m": [0, 0], "n": [100]}], [{f"s{i}": [R.randint(0, 100) for _ in range(5)] for i in range(2000)}]],
        examples=["Ali averages 85.0 (grade `A`); Sara averages 65.0 (`C`).", "An empty list gives `0.0` and `F`."],
        complexity={"time": "O(n log n)", "space": "O(n)"},
        approach="Loop over the dictionary items, compute the average, choose the grade with if / elif, then sort with a (-average, name) key.",
        tolerance=1e-9,
    )
    # ---------------------------------------------------------------- 4
    problem(
        slug="invoice-total", title="Invoice Total with Discount and Tax", difficulty="easy", minutes=15, topics=["lists", "conditions", "loops", "math"], tags=["business-rules", "fintech"], ds=["list", "tuple", "loop", "condition"], roles=ALL,
        statement="`items` is a list of `[name, unit_price, quantity]`. Compute the subtotal (sum of price * quantity). Apply a discount to the subtotal: 15% if the subtotal is more than 10000, otherwise 10% if it is more than 5000, otherwise none. Then add 17% sales tax on the discounted amount.\n\nReturn `[subtotal, discount_amount, tax_amount, total]`, each rounded to 2 decimals with `round()`.",
        constraints=["0 <= len(items) <= 1000", "0 <= unit_price <= 100000", "0 <= quantity <= 1000", "An empty invoice gives `[0.0, 0.0, 0.0, 0.0]`"],
        entry_point="invoice_total", signature="def invoice_total(items):",
        reference="def invoice_total(items):\n    subtotal = sum(p * q for _, p, q in items)\n    if subtotal > 10000:\n        rate = 0.15\n    elif subtotal > 5000:\n        rate = 0.10\n    else:\n        rate = 0.0\n    discount = subtotal * rate\n    taxable = subtotal - discount\n    tax = taxable * 0.17\n    return [round(subtotal, 2), round(discount, 2), round(tax, 2), round(taxable + tax, 2)]\n",
        visible=[[[["pen", 50, 10], ["book", 300, 2]]], [[["laptop", 6000, 1]]], [[]]],
        hidden=[[[["a", 10000, 1]]], [[["a", 10001, 1]]], [[["a", 5000, 1]]], [[["a", 5000.5, 1]]], [[["x", 19.99, 3], ["y", 4.5, 7]]], [[["big", 99999.99, 3]]], [[["z", 0, 100]]]],
        examples=["Subtotal 1100, no discount, tax 187, total 1287.", "Subtotal 6000 gets a 10% discount (600), tax is 17% of 5400."],
        complexity={"time": "O(n)", "space": "O(1)"},
        approach="Sum price * quantity in one loop, pick the discount rate with if / elif / else (note the boundaries: exactly 5000 or 10000 gets the lower rate), then apply tax to the discounted amount.",
        tolerance=0.011,
    )
    # ---------------------------------------------------------------- 5
    problem(
        slug="failed-logins", title="Suspicious Failed Logins", difficulty="medium", minutes=20, topics=["dictionaries", "loops", "conditions", "lists"], tags=["api-logic", "security", "grouping"], ds=["list", "dict", "set", "loop", "condition"], roles=BACK + ["ai-ml-engineer-intern"],
        statement="`events` is a list of `[user, result]` in time order, where `result` is `\"ok\"` or `\"fail\"`. A user is suspicious if they have 3 or more `\"fail\"` events IN A ROW (a successful login resets that user's streak; other users' events do not).\n\nReturn the sorted list of suspicious users, each once.",
        constraints=["0 <= len(events) <= 100000", "user is a non-empty string", "result is exactly `ok` or `fail`"],
        entry_point="failed_logins", signature="def failed_logins(events):",
        reference="def failed_logins(events):\n    streak = {}\n    flagged = set()\n    for user, result in events:\n        if result == 'fail':\n            streak[user] = streak.get(user, 0) + 1\n            if streak[user] >= 3:\n                flagged.add(user)\n        else:\n            streak[user] = 0\n    return sorted(flagged)\n",
        visible=[[[["ali", "fail"], ["ali", "fail"], ["ali", "fail"]]], [[["sara", "fail"], ["sara", "fail"], ["sara", "ok"], ["sara", "fail"]]], [[]]],
        hidden=[[[["a", "fail"], ["b", "fail"], ["a", "fail"], ["b", "fail"], ["a", "fail"]]], [[["a", "fail"], ["a", "fail"], ["a", "ok"], ["a", "fail"], ["a", "fail"], ["a", "fail"]]], [[["x", "ok"]]], [[["a", "fail"], ["a", "fail"], ["a", "ok"], ["a", "fail"], ["a", "fail"], ["a", "ok"], ["a", "fail"]]], [[["u", "fail"]] * 4], [[["b", "fail"], ["a", "fail"], ["a", "fail"], ["a", "fail"], ["b", "fail"], ["b", "fail"], ["b", "fail"]]], [[[f"u{i % 50}", "fail" if R.random() < 0.7 else "ok"] for i in range(10000)]]],
        examples=["`ali` fails three times in a row, so `[\"ali\"]`.", "`sara`'s streak is reset by `ok`, so nobody is flagged."],
        complexity={"time": "O(n)", "space": "O(u)"},
        approach="Keep a dict of current failure streaks per user. A failure increases the streak (flag the user at 3); a success resets it to 0. A set avoids duplicates.",
    )
    # ---------------------------------------------------------------- 6
    problem(
        slug="bank-ledger", title="Bank Ledger", difficulty="medium", minutes=25, topics=["dictionaries", "lists", "conditions", "loops"], tags=["fintech", "business-rules", "grouping"], ds=["list", "tuple", "dict", "loop", "condition"], roles=SW + ["data-scientist"],
        statement="`transactions` is a list of `[account, kind, amount]` where `kind` is `\"deposit\"` or `\"withdraw\"`. Every account starts at balance 0. Process the transactions in order:\n- a deposit adds `amount`;\n- a withdraw subtracts `amount` ONLY if the balance is enough; otherwise the transaction is rejected and the balance does not change.\n\nReturn `[balances, rejected]`, where `balances` is a dictionary account -> final balance (every account that appears is included) and `rejected` is the list of indexes (0-based) of rejected transactions.",
        constraints=["0 <= len(transactions) <= 50000", "amount is an integer, 1 <= amount <= 10^6", "An account that only has rejected withdrawals still appears with balance 0"],
        entry_point="bank_ledger", signature="def bank_ledger(transactions):",
        reference="def bank_ledger(transactions):\n    balances = {}\n    rejected = []\n    for i, (acct, kind, amount) in enumerate(transactions):\n        bal = balances.get(acct, 0)\n        if kind == 'deposit':\n            balances[acct] = bal + amount\n        elif bal >= amount:\n            balances[acct] = bal - amount\n        else:\n            balances[acct] = bal\n            rejected.append(i)\n    return [balances, rejected]\n",
        visible=[[[["A", "deposit", 100], ["A", "withdraw", 30], ["B", "withdraw", 10]]], [[["x", "deposit", 5], ["x", "withdraw", 5]]], [[]]],
        hidden=[[[["A", "withdraw", 1]]], [[["A", "deposit", 10], ["B", "deposit", 20], ["A", "withdraw", 11], ["B", "withdraw", 20]]], [[["a", "deposit", 1], ["a", "deposit", 1], ["a", "withdraw", 3]]], [[["q", "withdraw", 5], ["q", "deposit", 5], ["q", "withdraw", 5]]], [[["a", "deposit", 5], ["b", "withdraw", 1], ["a", "withdraw", 5], ["a", "withdraw", 1]]], [[["u" + str(i % 7), "deposit" if i % 3 else "withdraw", (i % 11) + 1] for i in range(5000)]]],
        examples=["A ends with 70; B never had money, so its withdrawal (index 2) is rejected.", "Withdrawing exactly the balance is allowed."],
        complexity={"time": "O(n)", "space": "O(a)"},
        approach="Walk through the list once with enumerate, keeping balances in a dict. Check the balance before a withdraw and record the index when it is rejected.",
    )
    # ---------------------------------------------------------------- 7
    problem(
        slug="custom-fizzbuzz", title="Custom FizzBuzz", difficulty="easy", minutes=10, topics=["loops", "conditions", "lists", "strings"], tags=["basics", "business-rules"], ds=["list", "tuple", "loop", "condition"], roles=ALL,
        statement="`rules` is a list of `[divisor, word]` pairs in priority order. For every number `i` from 1 to `n` (inclusive) build a string by appending `word` for each rule whose divisor divides `i` (in the order of the rules). If no rule matches, use `str(i)`.\n\nReturn the list of `n` strings. Classic FizzBuzz is `rules = [[3, \"Fizz\"], [5, \"Buzz\"]]`.",
        constraints=["0 <= n <= 20000", "0 <= len(rules) <= 6", "1 <= divisor <= 100"],
        entry_point="custom_fizzbuzz", signature="def custom_fizzbuzz(n, rules):",
        reference="def custom_fizzbuzz(n, rules):\n    out = []\n    for i in range(1, n + 1):\n        s = ''\n        for d, w in rules:\n            if i % d == 0:\n                s += w\n        out.append(s or str(i))\n    return out\n",
        visible=[[5, [[3, "Fizz"], [5, "Buzz"]]], [3, []], [0, [[2, "x"]]]],
        hidden=[[15, [[3, "Fizz"], [5, "Buzz"]]], [12, [[2, "Two"], [3, "Three"], [4, "Four"]]], [1, [[1, "One"]]], [10, [[5, "B"], [3, "A"]]], [7, [[7, "Seven"]]], [3000, [[3, "Fizz"], [5, "Buzz"], [7, "Bazz"]]]],
        examples=["`[\"1\", \"2\", \"Fizz\", \"4\", \"Buzz\"]` for n=5 with the classic rules.", "With no rules every number stays as text."],
        complexity={"time": "O(n * r)", "space": "O(n)"},
        approach="Nested loops: for each number check every rule with the modulo operator and join the matching words; fall back to the number.",
    )
    # ---------------------------------------------------------------- 8
    problem(
        slug="missing-numbers", title="Find the Missing Numbers", difficulty="easy", minutes=10, topics=["sets", "lists", "loops"], tags=["basics", "set-ops"], ds=["list", "set", "loop"], roles=ALL,
        statement="`nums` contains distinct integers that were taken from the range `1..n`. Return the sorted list of the numbers from `1` to `n` that are NOT in `nums`.",
        constraints=["1 <= n <= 100000", "0 <= len(nums) <= n", "Every value of nums is between 1 and n and appears once"],
        entry_point="missing_numbers", signature="def missing_numbers(nums, n):",
        reference="def missing_numbers(nums, n):\n    present = set(nums)\n    return [i for i in range(1, n + 1) if i not in present]\n",
        visible=[[[1, 2, 4], 5], [[], 3], [[1, 2, 3], 3]],
        hidden=[[[2], 2], [[5, 3, 1], 6], [[1], 1], [[10, 9, 8], 10], [list(range(2, 10001)), 10000], [list(range(1, 10001, 2)), 10000]],
        examples=["`3` and `5` are missing from `1..5`, so `[3, 5]`.", "Nothing is present, so all numbers are missing."],
        complexity={"time": "O(n)", "space": "O(n)"},
        approach="Put nums in a set for fast lookups, then loop through 1..n and keep the numbers that are absent.",
    )
    # ---------------------------------------------------------------- 9
    problem(
        slug="pair-sum-unique", title="Unique Pairs with a Given Sum", difficulty="medium", minutes=20, topics=["sets", "tuples", "lists", "sorting"], tags=["set-ops", "hashing"], ds=["list", "tuple", "set", "loop", "condition"], roles=ALL,
        statement="Given a list `nums` and an integer `target`, return all UNIQUE pairs `[a, b]` with `a <= b` and `a + b == target`, sorted ascending. Two pairs are the same if they contain the same two values. A value may be used twice only if it appears at least twice in `nums`.",
        constraints=["0 <= len(nums) <= 20000", "-10^6 <= nums[i], target <= 10^6", "Return a sorted list of `[a, b]` lists"],
        entry_point="pair_sum_unique", signature="def pair_sum_unique(nums, target):",
        reference="def pair_sum_unique(nums, target):\n    seen = set()\n    pairs = set()\n    for x in nums:\n        y = target - x\n        if y in seen:\n            pairs.add((min(x, y), max(x, y)))\n        seen.add(x)\n    return [list(p) for p in sorted(pairs)]\n",
        visible=[[[1, 2, 3, 4, 3], 6], [[2, 2, 2], 4], [[1], 2]],
        hidden=[[[], 0], [[0, 0], 0], [[5], 10], [[5, 5], 10], [[-1, 1, 2, -2, 0], 0], [[1, 5, 7, -1, 5], 6], [[3, 3, 3, 3], 6], [[R.randint(-500, 500) for _ in range(3000)], 17]],
        examples=["`2 + 4` and `3 + 3` (3 appears twice) give `[[2, 4], [3, 3]]`.", "`2` appears three times, so `[2, 2]` is valid once."],
        complexity={"time": "O(n log n)", "space": "O(n)"},
        approach="One pass with a set of seen values: if the complement was already seen, record the pair as a sorted tuple in another set (which removes duplicates), then sort the tuples.",
    )
    # ---------------------------------------------------------------- 10
    problem(
        slug="log-level-summary", title="Server Log Summary", difficulty="easy", minutes=15, topics=["dictionaries", "strings", "loops", "conditions"], tags=["api-logic", "strings", "grouping"], ds=["list", "dict", "loop", "condition"], roles=BACK + ["data-scientist"],
        statement="Each log line looks like `\"LEVEL: message\"`. Count how many lines have each level among `INFO`, `WARN` and `ERROR` (the level is the text before the FIRST colon, compared exactly). Lines with any other level, or without a colon, are ignored.\n\nReturn a dictionary with the keys `INFO`, `WARN` and `ERROR` (always all three, count 0 when absent).",
        constraints=["0 <= len(lines) <= 100000", "Level matching is case-sensitive", "The message may itself contain colons"],
        entry_point="log_level_summary", signature="def log_level_summary(lines):",
        reference="def log_level_summary(lines):\n    counts = {'INFO': 0, 'WARN': 0, 'ERROR': 0}\n    for line in lines:\n        if ':' not in line:\n            continue\n        level = line.split(':', 1)[0]\n        if level in counts:\n            counts[level] += 1\n    return counts\n",
        visible=[[["INFO: started", "ERROR: db down", "INFO: ok"]], [["DEBUG: x", "no colon"]], [[]]],
        hidden=[[["WARN: disk: 91%"]], [["info: lower case"]], [["ERROR:"]], [["ERROR : spaced"]], [[":empty level", "INFO:a", "INFO:b"]], [["INFO: x", "WARN: y", "ERROR: z"] * 3000]],
        examples=["Two `INFO` lines and one `ERROR` line.", "`DEBUG` and the line without a colon are ignored."],
        complexity={"time": "O(n)", "space": "O(1)"},
        approach="Start with a dict of zero counts, split each line once at the first colon (`split(':', 1)`) and count only the known levels.",
    )
    # ---------------------------------------------------------------- 11
    problem(
        slug="flatten-nested", title="Flatten a Nested List", difficulty="medium", minutes=20, topics=["lists", "recursion", "loops", "conditions"], tags=["recursion", "basics"], ds=["list", "loop", "condition"], roles=ALL,
        statement="`data` is a list that may contain integers and other lists (nested to any depth). Return one flat list with all the integers in their original left-to-right order.",
        constraints=["Total number of integers <= 20000", "Nesting depth <= 500", "Empty lists contribute nothing"],
        entry_point="flatten", signature="def flatten(data):",
        reference="def flatten(data):\n    out = []\n    stack = [iter(data)]\n    while stack:\n        for x in stack[-1]:\n            if isinstance(x, list):\n                stack.append(iter(x))\n                break\n            out.append(x)\n        else:\n            stack.pop()\n    return out\n",
        visible=[[[1, [2, [3, 4]], 5]], [[[], [[]]]], [[7]]],
        hidden=[[[]], [[[[[1]]]]], [[1, [2], 3, [4, [5, [6]]]]], [[[-1, [0]], [-2]]], [[[[] for _ in range(100)]]], [[[i, [i + 1, [i + 2]]] for i in range(2000)]]],
        examples=["`[1, [2, [3, 4]], 5]` becomes `[1, 2, 3, 4, 5]`.", "Empty lists vanish."],
        complexity={"time": "O(n)", "space": "O(d)"},
        approach="Use recursion or an explicit stack of iterators: when an element is a list, go into it, otherwise append the number.",
    )
    # ---------------------------------------------------------------- 12
    problem(
        slug="password-check", title="Password Rule Checker", difficulty="easy", minutes=10, topics=["strings", "conditions", "loops", "lists"], tags=["strings", "business-rules", "basics"], ds=["list", "loop", "condition"], roles=ALL,
        statement="Check a password against these rules and return the list of FAILED rule names, in exactly this order:\n1. `length`: at least 8 characters\n2. `lower`: has a lowercase letter\n3. `upper`: has an uppercase letter\n4. `digit`: has a digit\n5. `special`: has a character that is not a letter or digit\n6. `space`: contains NO space (fails if it has one)\n\nA valid password returns an empty list.",
        constraints=["0 <= len(password) <= 1000", "Use plain ASCII logic: letters a-z/A-Z and digits 0-9"],
        entry_point="password_check", signature="def password_check(password):",
        reference="def password_check(password):\n    failed = []\n    if len(password) < 8:\n        failed.append('length')\n    if not any('a' <= c <= 'z' for c in password):\n        failed.append('lower')\n    if not any('A' <= c <= 'Z' for c in password):\n        failed.append('upper')\n    if not any('0' <= c <= '9' for c in password):\n        failed.append('digit')\n    if not any(not (c.isascii() and c.isalnum()) for c in password):\n        failed.append('special')\n    if ' ' in password:\n        failed.append('space')\n    return failed\n",
        visible=[["Passw0rd!"], ["abc"], ["PASSWORD 1"]],
        hidden=[[""], ["12345678"], ["abcdefgh"], ["ABCDEFGH"], ["Abcdefg1"], ["Abcdef 1!"], ["!!!!!!!!"], ["aA1!aA1!" * 100]],
        examples=["`Passw0rd!` passes every rule: `[]`.", "`abc` is short and has no uppercase letter, digit or special character."],
        complexity={"time": "O(n)", "space": "O(1)"},
        approach="Check each rule with a small condition or `any(...)` over the characters and append the rule name when it fails, keeping the required order.",
    )
    # ---------------------------------------------------------------- 13
    problem(
        slug="merge-user-records", title="Merge User Records", difficulty="medium", minutes=25, topics=["dictionaries", "lists", "loops", "sorting"], tags=["data-cleaning", "grouping", "api-logic"], ds=["list", "dict", "loop", "condition"], roles=BACK + DATA,
        statement="`primary` and `updates` are lists of user dictionaries; each has an `\"id\"` and any other fields. Build one record per id: start from the record in `primary` and apply every update for that id in order (later values replace earlier values; new keys are added). Ids that only appear in `updates` are included too.\n\nReturn the merged records as a list sorted by `id`.",
        constraints=["0 <= len(primary), len(updates) <= 5000", "`id` is an integer; ids are unique inside `primary`", "`updates` may contain the same id several times"],
        entry_point="merge_user_records", signature="def merge_user_records(primary, updates):",
        reference="def merge_user_records(primary, updates):\n    merged = {}\n    for rec in primary:\n        merged[rec['id']] = dict(rec)\n    for rec in updates:\n        merged.setdefault(rec['id'], {}).update(rec)\n    return [merged[k] for k in sorted(merged)]\n",
        visible=[[[{"id": 2, "name": "Sara"}, {"id": 1, "name": "Ali"}], [{"id": 1, "city": "Lahore"}]], [[], [{"id": 5, "x": 1}]], [[{"id": 1, "a": 1}], []]],
        hidden=[[[], []], [[{"id": 1, "a": 1}], [{"id": 1, "a": 2}, {"id": 1, "a": 3}]], [[{"id": 3}, {"id": 1}], [{"id": 2, "n": "x"}]], [[{"id": 1, "a": 1, "b": 2}], [{"id": 1, "b": 9, "c": 7}]], [[{"id": 5, "k": "v"}], [{"id": 5, "k": "w"}, {"id": 4}]], [[{"id": i, "v": i} for i in range(2000, 0, -1)], [{"id": i, "w": i * 2} for i in range(1, 2001, 3)]]],
        examples=["Ali's record gets the new `city` key.", "An update for an unknown id creates a new record."],
        complexity={"time": "O(n log n)", "space": "O(n)"},
        approach="Index the primary records by id in a dict, apply updates with `dict.update`, then sort the keys to produce the final list.",
    )
    # ---------------------------------------------------------------- 14
    problem(
        slug="sliding-rate-limit", title="Rate Limiter", difficulty="medium", minutes=25, topics=["lists", "loops", "conditions", "queues"], tags=["api-logic", "simulation"], ds=["list", "loop", "condition"], roles=BACK,
        statement="An API allows at most `limit` accepted requests in any window of `window` seconds. `times` is the sorted list of request timestamps (integers, seconds). A request at time `t` is accepted only if fewer than `limit` ACCEPTED requests happened at times `> t - window` (so the window is `(t - window, t]`). Rejected requests do not count.\n\nReturn a list of booleans, `True` for accepted and `False` for rejected, one per request.",
        constraints=["0 <= len(times) <= 100000", "times is sorted ascending (duplicates allowed)", "1 <= limit <= 1000", "1 <= window <= 10^6"],
        entry_point="rate_limit", signature="def rate_limit(times, limit, window):",
        reference="def rate_limit(times, limit, window):\n    from collections import deque\n    accepted = deque()\n    out = []\n    for t in times:\n        while accepted and accepted[0] <= t - window:\n            accepted.popleft()\n        if len(accepted) < limit:\n            accepted.append(t)\n            out.append(True)\n        else:\n            out.append(False)\n    return out\n",
        visible=[[[1, 2, 3, 4], 2, 10], [[1, 5, 10], 1, 5], [[], 3, 3]],
        hidden=[[[1, 1, 1, 1], 2, 5], [[0, 10, 20], 1, 10], [[1, 2, 3, 11, 12, 13], 3, 10], [[5], 1, 1], [[1, 2, 3, 4, 5, 6], 2, 3], [sorted(R.randint(0, 5000) for _ in range(10000)), 5, 60]],
        examples=["The first two requests fit; the next two are rejected within 10 seconds.", "With limit 1 and window 5, a request exactly 5 seconds later is accepted."],
        complexity={"time": "O(n)", "space": "O(limit)"},
        approach="Keep a queue of accepted timestamps. Drop the ones that left the window, accept when the queue is shorter than the limit.",
    )
    # ---------------------------------------------------------------- 15
    problem(
        slug="department-stats", title="Department Salary Stats", difficulty="medium", minutes=25, topics=["dictionaries", "lists", "sorting", "loops"], tags=["grouping", "data-cleaning", "business-rules"], ds=["list", "tuple", "dict", "loop", "condition"], roles=BACK + DATA,
        statement="`employees` is a list of `[name, department, salary]`. For every department return `[department, headcount, average_salary, top_earner]` where the average is rounded to 2 decimals with `round()` and the top earner is the employee with the highest salary (if tied, the alphabetically smaller name).\n\nReturn the rows sorted by department name.",
        constraints=["0 <= len(employees) <= 20000", "salary is a non-negative integer", "Names are unique"],
        entry_point="department_stats", signature="def department_stats(employees):",
        reference="def department_stats(employees):\n    groups = {}\n    for name, dept, salary in employees:\n        groups.setdefault(dept, []).append((name, salary))\n    out = []\n    for dept in sorted(groups):\n        rows = groups[dept]\n        avg = round(sum(s for _, s in rows) / len(rows), 2)\n        top = min(rows, key=lambda r: (-r[1], r[0]))[0]\n        out.append([dept, len(rows), avg, top])\n    return out\n",
        visible=[[[["Ali", "IT", 100], ["Sara", "IT", 200], ["Zed", "HR", 50]]], [[]], [[["A", "X", 10], ["B", "X", 10]]]],
        hidden=[[[["a", "d", 1]]], [[["a", "d", 3], ["b", "d", 4]]], [[["m", "z", 100], ["n", "a", 50], ["o", "z", 100]]], [[["p", "Ops", 10], ["q", "Ops", 20], ["r", "Ops", 25]]], [[["a", "d", 5], ["b", "e", 5], ["c", "e", 7]]], [[[f"e{i}", f"d{i % 40}", R.randint(1000, 90000)] for i in range(3000)]]],
        examples=["IT has 2 people, average 150.0, top earner `Sara`.", "A tie on salary picks the alphabetically smaller name."],
        complexity={"time": "O(n log n)", "space": "O(n)"},
        approach="Group rows into a dict of lists by department, then for each department (sorted) compute count, mean and the top earner with a (-salary, name) key.",
        tolerance=1e-9,
    )
    # ---------------------------------------------------------------- 16
    problem(
        slug="clean-records", title="Clean Messy Records", difficulty="medium", minutes=25, topics=["lists", "sets", "strings", "conditions"], tags=["data-cleaning", "strings", "set-ops"], ds=["list", "tuple", "set", "loop", "condition"], roles=DATA + ["full-stack-developer"],
        statement="`rows` is a list of `[name, age, city]` where every value is a string and may have extra spaces. Clean it like this:\n1. strip spaces from every value;\n2. skip the row if the name or city is empty, or the age is not made only of digits;\n3. convert the age to an integer and skip the row if it is not between 1 and 120;\n4. format the name and the city with `.title()`;\n5. skip a row if the same `(name, city)` pair (compared in lowercase) was already kept.\n\nReturn the kept rows as `[name, age, city]` in their original order.",
        constraints=["0 <= len(rows) <= 20000", "Use `str.isdigit()` for the digits check", "The first occurrence of a duplicate pair is the one kept"],
        entry_point="clean_records", signature="def clean_records(rows):",
        reference="def clean_records(rows):\n    seen = set()\n    out = []\n    for name, age, city in rows:\n        name, age, city = name.strip(), age.strip(), city.strip()\n        if not name or not city or not age.isdigit():\n            continue\n        a = int(age)\n        if not 1 <= a <= 120:\n            continue\n        key = (name.lower(), city.lower())\n        if key in seen:\n            continue\n        seen.add(key)\n        out.append([name.title(), a, city.title()])\n    return out\n",
        visible=[[[[" ali khan ", " 25", "lahore "], ["", "30", "x"], ["Sara", "abc", "Lahore"]]], [[[" ali khan", "26", "LAHORE"], ["Ali Khan", "25", "lahore"]]], [[]]],
        hidden=[[[["a", "0", "b"]]], [[["a", "121", "b"]]], [[["a", "120", "b"], ["c", "1", "d"]]], [[["a", "12", "  "]]], [[["x", "5", "y"], ["X", "6", "Y"], ["x", "7", "z"]]], [[[" bob ", "-3", "k"]]], [[[f"user{i % 500}", str(i % 130), f"city{i % 7}"] for i in range(3000)]]],
        examples=["The first row becomes `[\"Ali Khan\", 25, \"Lahore\"]`; the others are invalid.", "The second row repeats the same name and city, so it is dropped."],
        complexity={"time": "O(n)", "space": "O(n)"},
        approach="Loop over the rows, strip and validate with conditions, convert the age, and use a set of lowercase (name, city) tuples to skip duplicates.",
    )
    # ---------------------------------------------------------------- 17
    problem(
        slug="leaderboard", title="Game Leaderboard", difficulty="medium", minutes=25, topics=["dictionaries", "sorting", "lists", "conditions"], tags=["grouping", "business-rules", "sorting"], ds=["list", "tuple", "dict", "loop", "condition"], roles=ALL,
        statement="`scores` is a list of `[player, points]` events (a player can appear many times; points add up). Return the leaderboard as a list of `[rank, player, total]`, sorted by total points (highest first) and then by player name. Players with the same total share the same rank (ranks are `1, 2, 2, 3...`, with no gaps after a tie).",
        constraints=["0 <= len(scores) <= 50000", "-1000 <= points <= 1000", "Totals can be negative"],
        entry_point="leaderboard", signature="def leaderboard(scores):",
        reference="def leaderboard(scores):\n    totals = {}\n    for player, pts in scores:\n        totals[player] = totals.get(player, 0) + pts\n    ordered = sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))\n    out = []\n    rank = 0\n    prev = None\n    for player, total in ordered:\n        if total != prev:\n            rank += 1\n            prev = total\n        out.append([rank, player, total])\n    return out\n",
        visible=[[[["a", 10], ["b", 20], ["a", 15]]], [[["x", 5], ["y", 5], ["z", 1]]], [[]]],
        hidden=[[[["a", 1]]], [[["a", 5], ["b", 5], ["c", 5]]], [[["a", -5], ["b", -5], ["c", 0]]], [[["m", 3], ["n", 2], ["m", -1], ["n", 0], ["o", 2]]], [[["p", 10], ["q", 9], ["r", 9], ["s", 8]]], [[[f"p{R.randint(0, 3000)}", R.randint(-1000, 1000)] for _ in range(5000)]]],
        examples=["`a` totals 25 and `b` totals 20, so `a` is rank 1.", "`x` and `y` tie at rank 1; `z` is rank 2 (dense ranking)."],
        complexity={"time": "O(n log n)", "space": "O(p)"},
        approach="Sum the points per player in a dict, sort by (-total, name) and assign dense ranks that only increase when the total changes.",
    )
    # ---------------------------------------------------------------- 18
    problem(
        slug="longest-consecutive", title="Longest Consecutive Run", difficulty="medium", minutes=25, topics=["sets", "lists", "loops", "conditions"], tags=["hashing", "set-ops"], ds=["list", "set", "loop", "condition"], roles=ALL,
        statement="Given an unsorted list of integers `nums`, return the length of the longest run of consecutive integers (like `4, 5, 6, 7`) that can be formed from its values. Duplicates are ignored. Aim for O(n) using a set instead of sorting.",
        constraints=["0 <= len(nums) <= 100000", "-10^9 <= nums[i] <= 10^9", "An empty list gives 0"],
        entry_point="longest_consecutive", signature="def longest_consecutive(nums):",
        reference="def longest_consecutive(nums):\n    s = set(nums)\n    best = 0\n    for x in s:\n        if x - 1 not in s:\n            y = x\n            while y + 1 in s:\n                y += 1\n            best = max(best, y - x + 1)\n    return best\n",
        visible=[[[100, 4, 200, 1, 3, 2]], [[1, 1, 1]], [[]]],
        hidden=[[[5]], [[1, 2, 2, 3, 3, 4]], [[-2, -1, 0, 1]], [[10, 5, 12, 3, 55, 30, 4, 11, 2]], [[9, 1, 4, 7, 3, -1, 0, 5, 8, -1, 6]], [[1, 3, 5, 7]], [list(range(10000))], [R.sample(range(-10**9, 10**9), 10000)]],
        examples=["`1, 2, 3, 4` is the longest run, so the answer is 4.", "Duplicates of `1` count once."],
        complexity={"time": "O(n)", "space": "O(n)"},
        approach="Put all numbers in a set. Only start counting from numbers whose predecessor is missing (run starts); extend while the next number exists.",
    )
    # ---------------------------------------------------------------- 19
    problem(
        slug="meeting-rooms", title="Minimum Meeting Rooms", difficulty="medium", minutes=30, topics=["lists", "sorting", "loops", "conditions"], tags=["sorting", "simulation"], ds=["list", "tuple", "loop", "condition"], roles=ALL,
        statement="`meetings` is a list of `[start, end]` times (with `start < end`). Two meetings overlap if one starts BEFORE the other ends; a meeting that starts exactly when another ends can use the same room. Return the minimum number of rooms needed to hold all meetings.",
        constraints=["0 <= len(meetings) <= 50000", "0 <= start < end <= 10^9"],
        entry_point="min_rooms", signature="def min_rooms(meetings):",
        reference="def min_rooms(meetings):\n    starts = sorted(m[0] for m in meetings)\n    ends = sorted(m[1] for m in meetings)\n    rooms = best = j = 0\n    for s in starts:\n        while ends[j] <= s:\n            j += 1\n            rooms -= 1\n        rooms += 1\n        best = max(best, rooms)\n    return best\n",
        visible=[[[[0, 30], [5, 10], [15, 20]]], [[[7, 10], [2, 4]]], [[]]],
        hidden=[[[[1, 2], [2, 3], [3, 4]]], [[[1, 5], [1, 5], [1, 5]]], [[[0, 10], [1, 2], [3, 4], [5, 6]]], [[[1, 10], [2, 3], [2, 4], [3, 5]]], [[[0, 1]]], [[[i, i + 1 + (i % 50)] for i in range(0, 5000)]]],
        examples=["The first meeting overlaps both others, so 2 rooms are needed.", "Back-to-back meetings can share a room."],
        complexity={"time": "O(n log n)", "space": "O(n)"},
        approach="Sort start times and end times separately and sweep: a new meeting needs a room unless an earlier meeting has already ended.",
    )
