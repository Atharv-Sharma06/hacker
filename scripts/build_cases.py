"""Generate tasks/<id>/cases.json.

Every case's expected value comes from tasks/<id>/reference.py, and the
reference is checked two ways before anything is written:

  * hand-written "expert" cases carry an expected value written by hand; the
    reference must agree with it (this is where the domain knowledge lives);
  * fuzz cases are cross-checked against an independent oracle (CPython's own
    stdlib where one exists, otherwise a second, deliberately naive
    implementation).

Any disagreement aborts the build. Run:  python scripts/build_cases.py
"""

import ast
import csv
import datetime as dt
import decimal
import importlib.util
import io
import json
import pathlib
import posixpath
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TASKS = ROOT / "tasks"
SEED = 20261030


def load_reference(task_id):
    spec = importlib.util.spec_from_file_location(f"ref_{task_id}", TASKS / task_id / "reference.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    meta = json.loads((TASKS / task_id / "task.json").read_text())
    return getattr(mod, meta["function"])


def run_ref(fn, args):
    try:
        return {"expected": fn(*args)}
    except ValueError:
        return {"expected_error": "ValueError"}


class Builder:
    def __init__(self, task_id):
        self.task_id = task_id
        self.fn = load_reference(task_id)
        self.cases = []
        self.seen = set()

    def add(self, args, tag, expected=..., error=None, note=None):
        key = json.dumps(args)
        if key in self.seen:
            return
        self.seen.add(key)
        got = run_ref(self.fn, args)
        if error is not None:
            want = {"expected_error": error}
        elif expected is not ...:
            want = {"expected": expected}
        else:
            want = None
        if want is not None and got != want:
            sys.exit(f"[{self.task_id}] reference disagrees on {args!r}: got {got}, hand-written {want}")
        case = {"id": f"{self.task_id}-{len(self.cases):03d}", "tag": tag, "args": args, **got}
        if note:
            case["note"] = note
        self.cases.append(case)

    def oracle(self, args, oracle_value, tag):
        got = run_ref(self.fn, args)
        if got != oracle_value:
            sys.exit(f"[{self.task_id}] reference disagrees with oracle on {args!r}: {got} vs {oracle_value}")
        self.add(args, tag)

    def write(self):
        out = TASKS / self.task_id / "cases.json"
        out.write_text(json.dumps(self.cases, indent=1, ensure_ascii=False) + "\n")
        tags = {}
        for c in self.cases:
            tags[c["tag"]] = tags.get(c["tag"], 0) + 1
        print(f"{self.task_id:26s} {len(self.cases):4d} cases  {tags}")


# --------------------------------------------------------------------------- semver
def build_semver(rng):
    b = Builder("semver_compare")
    expert = [
        ("1.0.0", "2.0.0", -1, "core"), ("2.0.0", "2.1.0", -1, "core"), ("2.1.0", "2.1.1", -1, "core"),
        ("1.10.0", "1.9.0", 1, "core-numeric"), ("10.0.0", "9.99.99", 1, "core-numeric"),
        ("1.0.0-alpha", "1.0.0", -1, "prerelease-vs-release"),
        ("1.0.0-rc.1", "1.0.0", -1, "prerelease-vs-release"),
        ("1.0.0-alpha", "1.0.0-alpha.1", -1, "prerelease-length"),
        ("1.0.0-alpha.1", "1.0.0-alpha.beta", -1, "numeric-before-alnum"),
        ("1.0.0-alpha.beta", "1.0.0-beta", -1, "prerelease-lexical"),
        ("1.0.0-beta", "1.0.0-beta.2", -1, "prerelease-length"),
        ("1.0.0-beta.2", "1.0.0-beta.11", -1, "prerelease-numeric"),
        ("1.0.0-beta.11", "1.0.0-rc.1", -1, "prerelease-lexical"),
        ("1.0.0-alpha.10", "1.0.0-alpha.9", 1, "prerelease-numeric"),
        ("1.0.0-1", "1.0.0-0A", -1, "numeric-before-alnum", "'0A' is alphanumeric"),
        ("1.0.0-2", "1.0.0-1-1", -1, "numeric-before-alnum", "'1-1' is alphanumeric"),
        ("1.0.0-99999999999999999999999", "1.0.0-100000000000000000000000", -1, "prerelease-bignum"),
        ("1.0.0-Alpha", "1.0.0-alpha", -1, "ascii-order", "'A' (65) sorts before 'a' (97)"),
        ("1.0.0-alpha-2", "1.0.0-alpha-10", 1, "ascii-order", "hyphenated identifier compares as text"),
        ("1.0.0-a.b.c.d", "1.0.0-a.b.c", 1, "prerelease-length"),
        ("1.0.0-x.7.z.92", "1.0.0-x.7.z.92", 0, "equal"),
        ("1.0.0+build.1", "1.0.0+build.2", 0, "build-ignored"),
        ("1.0.0+20130313144700", "1.0.0", 0, "build-ignored"),
        ("1.0.0-beta+exp.sha.5114f85", "1.0.0-beta", 0, "build-ignored"),
        ("1.0.0+build-1", "1.0.0", 0, "build-with-hyphen", "the '-' is inside build metadata, not a pre-release"),
        ("1.0.0+build-1", "1.0.0-rc.1", 1, "build-with-hyphen"),
        ("1.0.0-rc.1+build-9", "1.0.0-rc.1+build-1", 0, "build-with-hyphen"),
        ("1.0.0-0.3.7", "1.0.0-0.3.7.0", -1, "prerelease-length"),
        ("1.0.0-0", "1.0.0-a", -1, "numeric-before-alnum"),
        ("1.0.0--", "1.0.0-0", 1, "numeric-before-alnum", "'-' alone is an alphanumeric identifier"),
        ("123456789012345678901234567890.0.0", "123456789012345678901234567889.9.9", 1, "core-bignum"),
        ("0.0.0", "0.0.0-0", 1, "prerelease-vs-release"),
    ]
    for row in expert:
        a, c, want, tag = row[:4]
        note = row[4] if len(row) > 4 else None
        b.add([a, c], tag, want, note=note)
        b.add([c, a], tag, -want, note=note)

    ids = ["alpha", "beta", "rc", "0", "1", "2", "9", "10", "11", "0A", "a1", "x-y", "Z", "-"]
    def rand_v():
        v = f"{rng.randint(0, 3)}.{rng.randint(0, 3)}.{rng.randint(0, 3)}"
        if rng.random() < 0.8:
            v += "-" + ".".join(rng.choice(ids) for _ in range(rng.randint(1, 3)))
        if rng.random() < 0.3:
            v += "+" + rng.choice(["b1", "build-7", "exp.sha.5", "001"])
        return v
    # oracle: sort-key implementation written independently of reference.py
    def key(v):
        core = v.split("+")[0]
        head, sep, pre = core.partition("-")
        nums = tuple(int(x) for x in head.split("."))
        if not sep:
            return (nums, 1, ())
        return (nums, 0, tuple((0, int(p), "") if p.isdigit() else (1, 0, p) for p in pre.split(".")))
    for _ in range(140):
        a, c = rand_v(), rand_v()
        ka, kc = key(a), key(c)
        b.oracle([a, c], {"expected": (ka > kc) - (ka < kc)}, "fuzz")
    b.write()


# --------------------------------------------------------------------------- csv
def build_csv(rng):
    b = Builder("csv_parse")
    expert = [
        ("", [], "empty"),
        ("a", [["a"]], "basic"),
        ("a,b,c\n1,2,3", [["a", "b", "c"], ["1", "2", "3"]], "basic"),
        ("a,b\n", [["a", "b"]], "trailing-newline"),
        ("a,b\r\n", [["a", "b"]], "trailing-newline"),
        ("a,b\n\n", [["a", "b"], [""]], "blank-record"),
        ("\n", [[""]], "blank-record"),
        ("\n\n", [[""], [""]], "blank-record"),
        ("a\n\nb", [["a"], [""], ["b"]], "blank-record"),
        ("a,", [["a", ""]], "trailing-comma"),
        (",", [["", ""]], "trailing-comma"),
        (",,\n", [["", "", ""]], "trailing-comma"),
        ('""', [[""]], "quoted-empty"),
        ('"",""', [["", ""]], "quoted-empty"),
        ('"a,b",c', [["a,b", "c"]], "quoted-delimiter"),
        ('"line1\nline2",x', [["line1\nline2", "x"]], "quoted-newline"),
        ('"crlf\r\ninside"\r\nnext', [["crlf\r\ninside"], ["next"]], "quoted-newline"),
        ('"say ""hi"""', [['say "hi"']], "escaped-quote"),
        ('""""', [['"']], "escaped-quote"),
        ('""""""', [['""']], "escaped-quote"),
        ('a"b,c', [['a"b', "c"]], "bare-quote-literal"),
        ('ab",c', [['ab"', "c"]], "bare-quote-literal"),
        ('x""y', [['x""y']], "bare-quote-literal"),
        ("a\rb,c", [["a\rb", "c"]], "lone-cr"),
        ("a,b\r", [["a", "b\r"]], "lone-cr"),
        (" a , b ", [[" a ", " b "]], "whitespace-kept"),
        ('"a" ,b', None, "error-after-quote"),
        ('"a"b', None, "error-after-quote"),
        ('"a""', None, "error-unterminated"),
        ('"abc', None, "error-unterminated"),
        ('a,"b\n', None, "error-unterminated"),
        ('"a"\r', None, "error-after-quote"),
        ("é,ü\n日本,\"語\"", [["é", "ü"], ["日本", "語"]], "unicode"),
    ]
    for text, want, tag in expert:
        if want is None:
            b.add([text], tag, error="ValueError")
        else:
            b.add([text], tag, want)

    # oracle: csv module agrees with this grammar when no record is blank and
    # no field contains a lone CR; restrict fuzz to that subset.
    alphabet = ['a', 'b', ' ', 'x', 'é', '1']
    def rand_field():
        r = rng.random()
        if r < 0.5:
            return "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 4)))
        inner = "".join(rng.choice(alphabet + [',', '\n', '""', '\r\n']) for _ in range(rng.randint(0, 5)))
        return f'"{inner}"'
    for _ in range(120):
        recs = [",".join(rand_field() for _ in range(rng.randint(1, 4))) for _ in range(rng.randint(1, 4))]
        nl = rng.choice(["\n", "\r\n"])
        text = nl.join(recs) + (nl if rng.random() < 0.5 else "")
        rows = list(csv.reader(io.StringIO(text, newline=""), strict=True))
        b.oracle([text], {"expected": rows}, "fuzz")
    b.write()


# --------------------------------------------------------------------------- normpath
def build_normpath(rng):
    b = Builder("posix_normpath")
    expert = [
        ("", "."), (".", "."), ("./", "."), ("/", "/"), ("//", "//"), ("///", "/"), ("////", "/"),
        ("//a", "//a"), ("///a", "/a"), ("//a//b/", "//a/b"), ("/..", "/"), ("/../..", "/"),
        ("/../a", "/a"), ("//..", "//"), ("..", ".."), ("../..", "../.."), ("a/..", "."),
        ("a/../..", ".."), ("a/b/../../..", ".."), ("../a/..", ".."), ("./../a", "../a"),
        ("a/./b/.", "a/b"), ("a//b", "a/b"), ("a/b/", "a/b"), ("/a/b/c/../../d", "/a/d"),
        ("...", "..."), ("a/.../b", "a/.../b"), ("a/..b/../c", "a/c"), (".a/./.b", ".a/.b"),
        ("a b/ c", "a b/ c"), ("/ü/../é", "/é"), ("a/b/../../../../c", "../../c"),
    ]
    for path, want in expert:
        tag = "double-slash-root" if path.startswith("//") else ("dotdot" if ".." in path else "basic")
        b.add([path], tag, want)
    comps = ["a", "b", ".", "..", "", "...", "c d"]
    for _ in range(150):
        lead = rng.choice(["", "", "/", "//", "///"])
        p = lead + "/".join(rng.choice(comps) for _ in range(rng.randint(0, 6)))
        if rng.random() < 0.2:
            p += "/"
        b.oracle([p], {"expected": posixpath.normpath(p)}, "fuzz")
    b.write()


# --------------------------------------------------------------------------- decimal
def build_decimal(rng):
    b = Builder("decimal_round_half_even")
    expert = [
        ("2.675", 2, "2.68", "float-trap", "float(2.675) is 2.67499999..."),
        ("1.005", 2, "1.00", "float-trap", "exact tie, 0 is even"),
        ("1.015", 2, "1.02", "float-trap"),
        ("0.125", 2, "0.12", "tie-to-even"),
        ("0.135", 2, "0.14", "tie-to-even"),
        ("2.665", 2, "2.66", "tie-to-even"),
        ("0.5", 0, "0", "tie-to-even"), ("1.5", 0, "2", "tie-to-even"), ("2.5", 0, "2", "tie-to-even"),
        ("-2.5", 0, "-2", "tie-to-even"), ("-3.5", 0, "-4", "tie-to-even"),
        ("2.6750000000000000000001", 2, "2.68", "above-half"),
        ("2.6649999999999999999999", 2, "2.66", "below-half"),
        ("2.66500000", 2, "2.66", "tie-trailing-zeros"),
        ("9.995", 2, "10.00", "carry"), ("99.5", 0, "100", "carry"), ("-9.9999", 3, "-10.000", "carry"),
        ("-0.001", 2, "0.00", "negative-zero"), ("-0.5", 0, "0", "negative-zero"), ("-0", 0, "0", "negative-zero"),
        ("-0.000", 1, "0.0", "negative-zero"), ("-0.006", 2, "-0.01", "negative-small"),
        ("007.5", 0, "8", "leading-zeros"), ("000", 2, "0.00", "leading-zeros"),
        ("1.2", 4, "1.2000", "pad"), ("5", 3, "5.000", "pad"),
        ("123456789012345678901234567890.125", 2, "123456789012345678901234567890.12", "bignum"),
        ("0.000000000000000000000000000005", 29, "0.00000000000000000000000000000", "tiny-tie"),
        ("0.000000000000000000000000000015", 29, "0.00000000000000000000000000002", "tiny-tie"),
        ("15", 0, "15", "basic"), ("0.1", 1, "0.1", "basic"),
    ]
    for value, places, want, tag, *note in expert:
        b.add([value, places], tag, want, note=note[0] if note else None)
    ctx = decimal.Context(prec=200, rounding=decimal.ROUND_HALF_EVEN)
    for _ in range(150):
        ip = str(rng.randint(0, 10 ** rng.randint(0, 25)))
        if rng.random() < 0.2:
            ip = "0" * rng.randint(1, 3) + ip
        fd = rng.randint(0, 12)
        frac = "".join(rng.choice("0123456789") for _ in range(fd))
        if fd and rng.random() < 0.4:  # force an exact tie
            frac = frac[: rng.randint(0, fd - 1)] + "5"
        value = ("-" if rng.random() < 0.4 else "") + ip + ("." + frac if frac else "")
        places = rng.randint(0, 8)
        q = ctx.quantize(decimal.Decimal(value), decimal.Decimal(1).scaleb(-places))
        s = format(q, "f")
        if s.startswith("-") and q.is_zero():
            s = s[1:]
        b.oracle([value, places], {"expected": s}, "fuzz")
    b.write()


# --------------------------------------------------------------------------- cron
def brute_force_cron(expr, now):
    """Independent oracle: scan minute by minute. Only used with short horizons."""
    lo_hi = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 7)]
    fields = expr.split()
    sets = []
    for text, (lo, hi) in zip(fields, lo_hi):
        s = set()
        for item in text.split(","):
            step = 1
            if "/" in item:
                item, step = item.split("/")
                step = int(step)
                if item != "*" and "-" not in item:
                    item = f"{item}-{hi}"
            if item == "*":
                a, z = lo, hi
            elif "-" in item:
                a, z = map(int, item.split("-"))
            else:
                a = z = int(item)
            s |= {v for v in range(a, z + 1) if (v - a) % step == 0}
        sets.append(s)
    mi, ho, dm, mo, dw = sets
    dw = {0 if d == 7 else d for d in dw}
    restricted = not fields[2].startswith("*") and not fields[4].startswith("*")
    t = dt.datetime.strptime(now, "%Y-%m-%dT%H:%M")
    for _ in range(60 * 24 * 400):
        t += dt.timedelta(minutes=1)
        wd = (t.weekday() + 1) % 7
        dmatch = (t.day in dm) or (wd in dw) if restricted else (t.day in dm and wd in dw)
        if t.minute in mi and t.hour in ho and t.month in mo and dmatch:
            return t.strftime("%Y-%m-%dT%H:%M")
    return "NO-MATCH-WITHIN-HORIZON"


def build_cron(rng):
    b = Builder("cron_next_fire")
    expert = [
        ("* * * * *", "2026-10-30T03:15", "2026-10-30T03:16", "basic"),
        ("0 * * * *", "2026-10-30T03:00", "2026-10-30T04:00", "strictly-after"),
        ("59 23 31 12 *", "2026-12-31T23:59", "2027-12-31T23:59", "strictly-after"),
        ("*/15 * * * *", "2026-01-01T00:44", "2026-01-01T00:45", "step"),
        ("5/15 * * * *", "2026-01-01T00:51", "2026-01-01T01:05", "n-slash-step", "5/15 = 5,20,35,50"),
        ("10-40/10 9 * * *", "2026-01-01T09:41", "2026-01-02T09:10", "range-step"),
        ("0 0 1 * 1", "2026-06-02T00:00", "2026-06-08T00:00", "dom-dow-or", "both restricted: Monday OR the 1st"),
        ("0 0 13 * 5", "2026-01-01T00:00", "2026-01-02T00:00", "dom-dow-or", "every Friday plus every 13th"),
        ("0 0 13 * 5", "2026-02-07T00:00", "2026-02-13T00:00", "dom-dow-or"),
        ("0 0 */2 * 1", "2026-06-01T00:00", "2026-06-15T00:00", "star-step-is-unrestricted",
         "'*/2' starts with '*', so the day fields are ANDed: odd day AND Monday"),
        ("0 0 1 * */1", "2026-06-01T00:00", "2026-07-01T00:00", "star-step-is-unrestricted"),
        ("0 0 * * 7", "2026-10-25T12:00", "2026-11-01T00:00", "sunday-7"),
        ("0 0 * * 0", "2026-10-25T12:00", "2026-11-01T00:00", "sunday-0"),
        ("0 12 * * 5-7", "2026-10-26T00:00", "2026-10-30T12:00", "dow-range-to-7"),
        ("0 0 29 2 *", "2026-01-01T00:00", "2028-02-29T00:00", "leap-day"),
        ("0 0 29 2 *", "2096-03-01T00:00", "2104-02-29T00:00", "leap-day", "2100 is not a leap year"),
        ("0 0 30 2 *", "2026-01-01T00:00", None, "never"),
        ("0 0 31 4,6,9,11 *", "2026-01-01T00:00", None, "never"),
        ("0 0 31 2 1", "2026-02-01T00:00", "2026-02-02T00:00", "dom-dow-or", "the 31st never exists in Feb, but Mondays do"),
        ("30 2 * * *", "2026-10-30T02:29", "2026-10-30T02:30", "basic"),
        ("1,2,3 0 * * *", "2026-10-30T00:02", "2026-10-30T00:03", "list"),
        ("0 9-17/4 * * 1-5", "2026-10-30T17:01", "2026-11-02T09:00", "range-step"),
        ("0 0 1 1 *", "2026-12-31T23:59", "2027-01-01T00:00", "year-rollover"),
    ]
    for expr, now, want, tag, *note in expert:
        b.add([expr, now], tag, want, note=note[0] if note else None)

    def item(lo, hi):
        r = rng.random()
        if r < 0.3:
            return str(rng.randint(lo, hi))
        if r < 0.5:
            a = rng.randint(lo, hi)
            return f"{a}-{rng.randint(a, hi)}"
        if r < 0.65:
            return f"*/{rng.randint(2, 5)}"
        if r < 0.75:
            return f"{rng.randint(lo, hi)}/{rng.randint(2, 9)}"
        return ",".join(str(rng.randint(lo, hi)) for _ in range(rng.randint(2, 3)))
    added = 0
    while added < 70:
        expr = " ".join([
            item(0, 59), rng.choice(["*", item(0, 23)]),
            rng.choice(["*", item(1, 31)]), rng.choice(["*", "*", item(1, 12)]),
            rng.choice(["*", item(0, 7)]),
        ])
        now = dt.datetime(2026, 1, 1) + dt.timedelta(minutes=rng.randint(0, 60 * 24 * 365))
        now_s = now.strftime("%Y-%m-%dT%H:%M")
        oracle = brute_force_cron(expr, now_s)
        if oracle == "NO-MATCH-WITHIN-HORIZON":
            continue
        b.oracle([expr, now_s], {"expected": oracle}, "fuzz")
        added += 1
    b.write()


# --------------------------------------------------------------------------- python int literal
def literal_oracle(s):
    """CPython's own parser, restricted to strings over a safe alphabet."""
    if not s or any(c not in "0123456789abcdefABCDEFxXoObB_" for c in s):
        raise AssertionError(s)
    try:
        node = ast.parse(s, mode="eval").body
    except SyntaxError:
        return False
    return isinstance(node, ast.Constant) and type(node.value) is int


def build_int_literal(rng):
    b = Builder("python_int_literal")
    expert = [
        ("0", True), ("00", True), ("000", True), ("0_0", True), ("00_0", True), ("0_00", True),
        ("01", False), ("007", False), ("0_7", False), ("1", True), ("10", True), ("1_000_000", True),
        ("1__0", False), ("_1", False), ("1_", False), ("0x_f", True), ("0x_", False), ("0x", False),
        ("0xDEAD_beef", True), ("0XFF", True), ("0b1010", True), ("0B1", True), ("0b2", False),
        ("0b_1_0", True), ("0b1_", False), ("0o17", True), ("0O7", True), ("0o8", False), ("0o_7", True),
        ("0x__1", False), ("0_x1", False), ("0xg", False), ("1e5", False), ("1j", False), ("1.0", False),
        ("1L", False), ("0l", False), ("", False), (" 1", False), ("1 ", False), ("+1", False),
        ("-1", False), ("1\n", False), ("١", False), ("１", False), ("1٢", False),
        ("0o", False), ("0b", False), ("0_", False), ("_", False), ("9" * 400, True),
    ]
    for s, want in expert:
        if any(c in s for c in " +-\n") or any(ord(c) > 127 for c in s):
            tag = "int()-accepts-but-grammar-rejects"
        elif s.lower().startswith(("0x", "0b", "0o")):
            tag = "prefixed"
        elif "_" in s:
            tag = "underscores"
        elif s.startswith("0"):
            tag = "leading-zero"
        else:
            tag = "basic"
        b.add([s], tag, want)
    pieces = ["0", "1", "7", "9", "_", "x", "b", "o", "X", "B", "O", "f", "a", "e", "00"]
    while len(b.cases) < 200:
        s = "".join(rng.choice(pieces) for _ in range(rng.randint(1, 5)))
        if rng.random() < 0.4:
            s = rng.choice(["0x", "0b", "0o"]) + s
        b.oracle([s], {"expected": literal_oracle(s)}, "fuzz")
    b.write()


# --------------------------------------------------------------------------- iso week
def build_iso_week(rng):
    b = Builder("iso_week")
    expert = [
        ((2021, 1, 3), [2020, 53], "year-boundary"), ((2021, 1, 4), [2021, 1], "year-boundary"),
        ((2024, 12, 30), [2025, 1], "year-boundary"), ((2024, 12, 29), [2024, 52], "year-boundary"),
        ((2026, 12, 31), [2026, 53], "week-53"), ((2027, 1, 1), [2026, 53], "year-boundary"),
        ((2015, 12, 31), [2015, 53], "week-53"), ((2016, 1, 3), [2015, 53], "year-boundary"),
        ((2008, 12, 29), [2009, 1], "year-boundary"), ((2010, 1, 3), [2009, 53], "year-boundary"),
        ((1, 1, 1), [1, 1], "range-limit"), ((9999, 12, 31), [9999, 52], "range-limit"),
        ((2000, 2, 29), [2000, 9], "leap"), ((1900, 3, 1), [1900, 9], "century-non-leap"),
        ((2100, 12, 31), [2100, 52], "century-non-leap"), ((2026, 10, 30), [2026, 44], "basic"),
    ]
    for args, want, tag in expert:
        b.add(list(args), tag, want)
    for _ in range(120):
        if rng.random() < 0.6:  # concentrate on year boundaries
            y = rng.randint(1, 9998)
            d = dt.date(y, 12, 25) + dt.timedelta(days=rng.randint(0, 13))
        else:
            d = dt.date.fromordinal(rng.randint(1, dt.date(9999, 12, 31).toordinal()))
        iy, iw, _ = d.isocalendar()
        b.oracle([d.year, d.month, d.day], {"expected": [iy, iw]}, "fuzz")
    b.write()


if __name__ == "__main__":
    for fn in (build_semver, build_csv, build_normpath, build_decimal, build_cron, build_int_literal, build_iso_week):
        fn(random.Random(SEED))
