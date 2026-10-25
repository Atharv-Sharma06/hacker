"""Executed in a separate interpreter: python -I _child.py CANDIDATE CASES FUNCTION OUT."""

import builtins
import json
import signal
import sys
import traceback

PER_CASE_SECONDS = 5


def normalize(value):
    if isinstance(value, tuple):
        value = list(value)
    if isinstance(value, list):
        return [normalize(v) for v in value]
    return value


def main():
    candidate, cases_path, function, out_path = sys.argv[1:5]
    real_stdout = sys.stdout
    sys.stdout = sys.stderr  # candidate prints must not corrupt anything
    results = {"load_error": None, "cases": []}
    try:
        namespace = {"__name__": "candidate"}
        with open(candidate) as f:
            exec(compile(f.read(), "candidate.py", "exec"), namespace)
        fn = namespace[function]
    except BaseException:
        results["load_error"] = traceback.format_exc(limit=3)[-2000:]
        _write(out_path, results)
        return

    def on_alarm(signum, frame):
        raise TimeoutError(f"case exceeded {PER_CASE_SECONDS}s")

    signal.signal(signal.SIGALRM, on_alarm)
    with open(cases_path) as f:
        cases = json.load(f)
    for case in cases:
        rec = {"id": case["id"]}
        signal.setitimer(signal.ITIMER_REAL, PER_CASE_SECONDS)
        try:
            got = fn(*case["args"])
            signal.setitimer(signal.ITIMER_REAL, 0)
            if "expected_error" in case:
                rec["passed"] = False
                rec["got"] = _safe(normalize(got))
            else:
                got_n = normalize(got)
                rec["passed"] = json.dumps(got_n) == json.dumps(case["expected"])
                if not rec["passed"]:
                    rec["got"] = _safe(got_n)
        except BaseException as e:  # includes TimeoutError, RecursionError, SystemExit
            signal.setitimer(signal.ITIMER_REAL, 0)
            expected = getattr(builtins, case.get("expected_error", ""), None)
            rec["passed"] = isinstance(expected, type) and isinstance(e, expected)
            if not rec["passed"]:
                rec["error"] = f"{type(e).__name__}: {e}"[:300]
        results["cases"].append(rec)
    sys.stdout = real_stdout
    _write(out_path, results)


def _safe(value):
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return repr(value)[:300]


def _write(path, data):
    with open(path, "w") as f:
        json.dump(data, f)


if __name__ == "__main__":
    main()
