"""Deliberately WRONG solutions for the screening-style problems (trusted test fixtures). Hidden tests must catch each one."""


def m(name, code, slow=False):
    d = {"name": name, "code": code}
    if slow:
        d["slow"] = True
    return d


MUTANTS_SCREENING = {
    "unique-keep-order": [
        m("sorts instead of keeping order", "def unique_keep_order(items):\n    return sorted(set(items))\n"),
        m("keeps the last occurrence", "def unique_keep_order(items):\n    seen = set()\n    out = []\n    for x in reversed(items):\n        if x not in seen:\n            seen.add(x)\n            out.append(x)\n    return out[::-1]\n"),
    ],
    "common-elements": [
        m("keeps duplicates", "def common_elements(a, b):\n    return sorted(x for x in a if x in b)\n"),
        m("union instead of intersection", "def common_elements(a, b):\n    return sorted(set(a) | set(b))\n"),
    ],
    "grade-report": [
        m("strict > at the boundaries", "def grade_report(marks):\n    rows = []\n    for name, ms in marks.items():\n        avg = round(sum(ms) / len(ms), 2) if ms else 0.0\n        g = 'A' if avg > 85 else 'B' if avg > 70 else 'C' if avg > 50 else 'F'\n        rows.append([name, avg, g])\n    rows.sort(key=lambda r: (-r[1], r[0]))\n    return rows\n"),
        m("lowest average first", "def grade_report(marks):\n    rows = []\n    for name, ms in marks.items():\n        avg = round(sum(ms) / len(ms), 2) if ms else 0.0\n        g = 'A' if avg >= 85 else 'B' if avg >= 70 else 'C' if avg >= 50 else 'F'\n        rows.append([name, avg, g])\n    rows.sort(key=lambda r: (r[1], r[0]))\n    return rows\n"),
    ],
    "invoice-total": [
        m(">= at the discount boundaries", "def invoice_total(items):\n    subtotal = sum(p * q for _, p, q in items)\n    rate = 0.15 if subtotal >= 10000 else 0.10 if subtotal >= 5000 else 0.0\n    discount = subtotal * rate\n    taxable = subtotal - discount\n    tax = taxable * 0.17\n    return [round(subtotal, 2), round(discount, 2), round(tax, 2), round(taxable + tax, 2)]\n"),
        m("tax on the undiscounted subtotal", "def invoice_total(items):\n    subtotal = sum(p * q for _, p, q in items)\n    rate = 0.15 if subtotal > 10000 else 0.10 if subtotal > 5000 else 0.0\n    discount = subtotal * rate\n    tax = subtotal * 0.17\n    return [round(subtotal, 2), round(discount, 2), round(tax, 2), round(subtotal - discount + tax, 2)]\n"),
    ],
    "failed-logins": [
        m("counts total failures, not consecutive", "def failed_logins(events):\n    c = {}\n    for u, r in events:\n        if r == 'fail':\n            c[u] = c.get(u, 0) + 1\n    return sorted(u for u, n in c.items() if n >= 3)\n"),
        m("one shared streak for all users", "def failed_logins(events):\n    streak = 0\n    flagged = set()\n    for u, r in events:\n        if r == 'fail':\n            streak += 1\n            if streak >= 3:\n                flagged.add(u)\n        else:\n            streak = 0\n    return sorted(flagged)\n"),
    ],
    "bank-ledger": [
        m("allows overdrafts", "def bank_ledger(transactions):\n    b = {}\n    for a, k, x in transactions:\n        b[a] = b.get(a, 0) + (x if k == 'deposit' else -x)\n    return [b, []]\n"),
        m("rejects a withdrawal of the whole balance", "def bank_ledger(transactions):\n    b, rej = {}, []\n    for i, (a, k, x) in enumerate(transactions):\n        bal = b.get(a, 0)\n        if k == 'deposit':\n            b[a] = bal + x\n        elif bal > x:\n            b[a] = bal - x\n        else:\n            b[a] = bal\n            rej.append(i)\n    return [b, rej]\n"),
    ],
    "custom-fizzbuzz": [
        m("only the first matching rule", "def custom_fizzbuzz(n, rules):\n    out = []\n    for i in range(1, n + 1):\n        s = ''\n        for d, w in rules:\n            if i % d == 0:\n                s = w\n                break\n        out.append(s or str(i))\n    return out\n"),
        m("off by one (stops before n)", "def custom_fizzbuzz(n, rules):\n    out = []\n    for i in range(1, n):\n        s = ''\n        for d, w in rules:\n            if i % d == 0:\n                s += w\n        out.append(s or str(i))\n    return out\n"),
    ],
    "missing-numbers": [
        m("forgets n", "def missing_numbers(nums, n):\n    s = set(nums)\n    return [i for i in range(1, n) if i not in s]\n"),
        m("starts at 0", "def missing_numbers(nums, n):\n    s = set(nums)\n    return [i for i in range(0, n + 1) if i not in s]\n"),
    ],
    "pair-sum-unique": [
        m("uses one element twice", "def pair_sum_unique(nums, target):\n    s = set(nums)\n    return [list(p) for p in sorted({(min(x, target - x), max(x, target - x)) for x in s if target - x in s})]\n"),
        m("returns duplicate pairs", "def pair_sum_unique(nums, target):\n    seen = set()\n    out = []\n    for x in nums:\n        y = target - x\n        if y in seen:\n            out.append([min(x, y), max(x, y)])\n        seen.add(x)\n    return sorted(out)\n"),
    ],
    "log-level-summary": [
        m("case-insensitive levels", "def log_level_summary(lines):\n    c = {'INFO': 0, 'WARN': 0, 'ERROR': 0}\n    for line in lines:\n        if ':' in line:\n            lv = line.split(':', 1)[0].upper()\n            if lv in c:\n                c[lv] += 1\n    return c\n"),
        m("searches the whole line", "def log_level_summary(lines):\n    c = {'INFO': 0, 'WARN': 0, 'ERROR': 0}\n    for line in lines:\n        for lv in c:\n            if lv in line:\n                c[lv] += 1\n    return c\n"),
    ],
    "flatten-nested": [
        m("flattens only one level", "def flatten(data):\n    out = []\n    for x in data:\n        if isinstance(x, list):\n            out.extend(y for y in x if not isinstance(y, list))\n        else:\n            out.append(x)\n    return out\n"),
        m("sorts the result", "def flatten(data):\n    out = []\n    def go(d):\n        for x in d:\n            if isinstance(x, list):\n                go(x)\n            else:\n                out.append(x)\n    go(data)\n    return sorted(out)\n"),
    ],
    "password-check": [
        m("wrong rule order", "def password_check(password):\n    f = []\n    if len(password) < 8:\n        f.append('length')\n    if not any('a' <= c <= 'z' for c in password):\n        f.append('lower')\n    if not any('0' <= c <= '9' for c in password):\n        f.append('digit')\n    if not any('A' <= c <= 'Z' for c in password):\n        f.append('upper')\n    if not any(not (c.isascii() and c.isalnum()) for c in password):\n        f.append('special')\n    if ' ' in password:\n        f.append('space')\n    return f\n"),
        m("ignores spaces", "def password_check(password):\n    f = []\n    if len(password) < 8:\n        f.append('length')\n    if not any('a' <= c <= 'z' for c in password):\n        f.append('lower')\n    if not any('A' <= c <= 'Z' for c in password):\n        f.append('upper')\n    if not any('0' <= c <= '9' for c in password):\n        f.append('digit')\n    if not any(not (c.isascii() and c.isalnum()) for c in password):\n        f.append('special')\n    return f\n"),
    ],
    "merge-user-records": [
        m("first value wins", "def merge_user_records(primary, updates):\n    merged = {}\n    for rec in primary + updates:\n        d = merged.setdefault(rec['id'], {})\n        for k, v in rec.items():\n            d.setdefault(k, v)\n    return [merged[k] for k in sorted(merged)]\n"),
        m("drops ids that only appear in updates", "def merge_user_records(primary, updates):\n    merged = {r['id']: dict(r) for r in primary}\n    for rec in updates:\n        if rec['id'] in merged:\n            merged[rec['id']].update(rec)\n    return [merged[k] for k in sorted(merged)]\n"),
    ],
    "sliding-rate-limit": [
        m("rejected requests also count", "def rate_limit(times, limit, window):\n    seen = []\n    out = []\n    for t in times:\n        seen = [x for x in seen if x > t - window]\n        out.append(len(seen) < limit)\n        seen.append(t)\n    return out\n"),
        m("window boundary is inclusive", "def rate_limit(times, limit, window):\n    acc = []\n    out = []\n    for t in times:\n        acc = [x for x in acc if x >= t - window]\n        if len(acc) < limit:\n            acc.append(t)\n            out.append(True)\n        else:\n            out.append(False)\n    return out\n"),
    ],
    "department-stats": [
        m("ties pick the larger name", "def department_stats(employees):\n    g = {}\n    for n, d, s in employees:\n        g.setdefault(d, []).append((n, s))\n    out = []\n    for d in sorted(g):\n        r = g[d]\n        out.append([d, len(r), round(sum(s for _, s in r) / len(r), 2), max(r, key=lambda x: (x[1], x[0]))[0]])\n    return out\n"),
        m("integer average", "def department_stats(employees):\n    g = {}\n    for n, d, s in employees:\n        g.setdefault(d, []).append((n, s))\n    out = []\n    for d in sorted(g):\n        r = g[d]\n        out.append([d, len(r), sum(s for _, s in r) // len(r), min(r, key=lambda x: (-x[1], x[0]))[0]])\n    return out\n"),
    ],
    "clean-records": [
        m("duplicates are case-sensitive", "def clean_records(rows):\n    seen, out = set(), []\n    for n, a, c in rows:\n        n, a, c = n.strip(), a.strip(), c.strip()\n        if not n or not c or not a.isdigit() or not 1 <= int(a) <= 120:\n            continue\n        if (n, c) in seen:\n            continue\n        seen.add((n, c))\n        out.append([n.title(), int(a), c.title()])\n    return out\n"),
        m("allows age 0", "def clean_records(rows):\n    seen, out = set(), []\n    for n, a, c in rows:\n        n, a, c = n.strip(), a.strip(), c.strip()\n        if not n or not c or not a.isdigit() or not 0 <= int(a) <= 120:\n            continue\n        k = (n.lower(), c.lower())\n        if k in seen:\n            continue\n        seen.add(k)\n        out.append([n.title(), int(a), c.title()])\n    return out\n"),
    ],
    "leaderboard": [
        m("competition ranking with gaps", "def leaderboard(scores):\n    t = {}\n    for p, x in scores:\n        t[p] = t.get(p, 0) + x\n    rows = sorted(t.items(), key=lambda kv: (-kv[1], kv[0]))\n    out = []\n    for i, (p, v) in enumerate(rows):\n        rank = i + 1 if i == 0 or v != rows[i - 1][1] else out[-1][0]\n        out.append([rank, p, v])\n    return out\n"),
        m("ties not sorted by name", "def leaderboard(scores):\n    t = {}\n    for p, x in scores:\n        t[p] = t.get(p, 0) + x\n    rows = sorted(t.items(), key=lambda kv: -kv[1])\n    out, rank, prev = [], 0, None\n    for p, v in rows:\n        if v != prev:\n            rank += 1\n            prev = v\n        out.append([rank, p, v])\n    return out\n"),
    ],
    "longest-consecutive": [
        m("counts duplicates in the run", "def longest_consecutive(nums):\n    if not nums:\n        return 0\n    a = sorted(nums)\n    best = cur = 1\n    for i in range(1, len(a)):\n        cur = cur + 1 if a[i] == a[i - 1] + 1 or a[i] == a[i - 1] else 1\n        best = max(best, cur)\n    return best\n"),
        m("re-counts every run from every number (too slow)", "def longest_consecutive(nums):\n    s = set(nums)\n    best = 0\n    for x in s:\n        y = x\n        while y + 1 in s:\n            y += 1\n        best = max(best, y - x + 1)\n    return best\n", slow=True),
    ],
    "meeting-rooms": [
        m("touching meetings need separate rooms", "def min_rooms(meetings):\n    starts = sorted(x[0] for x in meetings)\n    ends = sorted(x[1] for x in meetings)\n    rooms = best = j = 0\n    for s in starts:\n        while ends[j] < s:\n            j += 1\n            rooms -= 1\n        rooms += 1\n        best = max(best, rooms)\n    return best\n"),
        m("one room per meeting", "def min_rooms(meetings):\n    return len(meetings)\n"),
    ],
    "inventory-restock": [
        m("ignores items missing from stock", "def inventory_restock(stock, minimum):\n    return [[i, minimum[i] - stock[i]] for i in sorted(minimum) if i in stock and stock[i] < minimum[i]]\n"),
        m("lists items that are exactly at the minimum", "def inventory_restock(stock, minimum):\n    return [[i, minimum[i] - stock.get(i, 0)] for i in sorted(minimum) if stock.get(i, 0) <= minimum[i]]\n"),
    ],
    "primes-upto": [
        m("treats 1 as prime", "def primes_upto(n):\n    return [i for i in range(1, n + 1) if all(i % d for d in range(2, int(i ** 0.5) + 1))]\n"),
        m("leaves out n itself", "def primes_upto(n):\n    return [i for i in range(2, n) if all(i % d for d in range(2, int(i ** 0.5) + 1))]\n"),
    ],
    "run-length-encode": [
        m("writes 1 for single characters", "def rle(s):\n    out, i = [], 0\n    while i < len(s):\n        j = i\n        while j < len(s) and s[j] == s[i]:\n            j += 1\n        out.append(s[i] + str(j - i))\n        i = j\n    return ''.join(out)\n"),
        m("counts a letter across the whole string", "def rle(s):\n    from collections import Counter\n    c = Counter(s)\n    return ''.join(ch + (str(n) if n > 1 else '') for ch, n in c.items())\n"),
    ],
    "roman-to-int": [
        m("only adds", "def roman_to_int(s):\n    v = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}\n    return sum(v[c] for c in s)\n"),
        m("handles only IV and IX", "def roman_to_int(s):\n    v = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}\n    t = 0\n    for i, c in enumerate(s):\n        if c == 'I' and i + 1 < len(s) and s[i + 1] in 'VX':\n            t -= 1\n        else:\n            t += v[c]\n    return t\n"),
    ],
    "palindrome-filter": [
        m("case-sensitive", "def palindrome_filter(phrases):\n    seen, out = set(), []\n    for p in phrases:\n        if p in seen:\n            continue\n        c = [x for x in p if x.isascii() and x.isalnum()]\n        if c and c == c[::-1]:\n            seen.add(p)\n            out.append(p)\n    return out\n"),
        m("does not remove duplicates", "def palindrome_filter(phrases):\n    out = []\n    for p in phrases:\n        c = [x.lower() for x in p if x.isascii() and x.isalnum()]\n        if c and c == c[::-1]:\n            out.append(p)\n    return out\n"),
        m("keeps punctuation", "def palindrome_filter(phrases):\n    seen, out = set(), []\n    for p in phrases:\n        if p in seen:\n            continue\n        c = p.lower()\n        if c and c == c[::-1]:\n            seen.add(p)\n            out.append(p)\n    return out\n"),
    ],
    "moving-average": [
        m("misses the last window", "def moving_average(values, k):\n    if k > len(values):\n        return []\n    return [round(sum(values[i:i + k]) / k, 2) for i in range(len(values) - k)]\n"),
        m("integer division", "def moving_average(values, k):\n    if k > len(values):\n        return []\n    return [sum(values[i:i + k]) // k for i in range(len(values) - k + 1)]\n"),
    ],
    "cart-by-category": [
        m("repeats product names", "def cart_by_category(cart):\n    t, n = {}, {}\n    for p, c, pr, q in cart:\n        t[c] = t.get(c, 0) + pr * q\n        n.setdefault(c, []).append(p)\n    rows = [[c, t[c], sorted(n[c])] for c in t]\n    rows.sort(key=lambda r: (-r[1], r[0]))\n    return rows\n"),
        m("sorts by category name only", "def cart_by_category(cart):\n    t, n = {}, {}\n    for p, c, pr, q in cart:\n        t[c] = t.get(c, 0) + pr * q\n        n.setdefault(c, set()).add(p)\n    return [[c, t[c], sorted(n[c])] for c in sorted(t)]\n"),
    ],
    "matrix-spiral": [
        m("single row or column read twice", "def spiral_order(matrix):\n    out = []\n    if not matrix or not matrix[0]:\n        return out\n    top, bottom, left, right = 0, len(matrix) - 1, 0, len(matrix[0]) - 1\n    while top <= bottom and left <= right:\n        for c in range(left, right + 1):\n            out.append(matrix[top][c])\n        for r in range(top + 1, bottom + 1):\n            out.append(matrix[r][right])\n        for c in range(right - 1, left - 1, -1):\n            out.append(matrix[bottom][c])\n        for r in range(bottom - 1, top, -1):\n            out.append(matrix[r][left])\n        top, bottom, left, right = top + 1, bottom - 1, left + 1, right - 1\n    return out\n"),
        m("goes down first", "def spiral_order(matrix):\n    out = []\n    if not matrix or not matrix[0]:\n        return out\n    for c in range(len(matrix[0])):\n        for r in range(len(matrix)):\n            out.append(matrix[r][c])\n    return out\n"),
    ],
    "first-unique-char": [
        m("returns the character instead of the index", "def first_unique(s):\n    for i, ch in enumerate(s):\n        if s.count(ch) == 1:\n            return ch\n    return -1\n"),
        m("returns 0 when nothing is unique", "def first_unique(s):\n    for i, ch in enumerate(s):\n        if s.count(ch) == 1:\n            return i\n    return 0\n"),
    ],
}
