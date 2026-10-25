from . import policy, sandbox
from .extract import extract_code


def grade(task, response: str) -> dict:
    """Grade one response. A task counts as solved only if every case passes."""
    result = {"task": task.id, "solved": False, "case_accuracy": 0.0, "status": "ok",
              "violations": [], "failed": [], "tags": {}}
    code = extract_code(response, task.function)
    if code is None:
        result["status"] = "no_code"
        return result
    violations = policy.check(code, task.forbidden_imports)
    if violations:
        status = "syntax_error" if violations[0].startswith("syntax error") else "policy_violation"
        result.update(status=status, violations=violations)
        return result
    run = sandbox.run_cases(code, task)
    if run["load_error"]:
        result.update(status="load_error", error=run["load_error"])
        return result

    by_id = {c["id"]: c for c in task.cases}
    passed = 0
    for rec in run["cases"]:
        case = by_id[rec["id"]]
        tag = result["tags"].setdefault(case["tag"], {"passed": 0, "total": 0})
        tag["total"] += 1
        if rec["passed"]:
            passed += 1
            tag["passed"] += 1
        else:
            failure = {"id": case["id"], "tag": case["tag"], "args": case["args"]}
            failure["expected"] = case.get("expected", f"raises {case.get('expected_error')}")
            for key in ("got", "error"):
                if key in rec:
                    failure[key] = rec[key]
            if "note" in case:
                failure["note"] = case["note"]
            result["failed"].append(failure)
    result["case_accuracy"] = passed / len(task.cases)
    result["solved"] = passed == len(task.cases)
    return result
