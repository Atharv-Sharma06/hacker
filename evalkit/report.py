import json
from collections import defaultdict


def _agg(results):
    by_task = defaultdict(list)
    for r in results:
        by_task[r["task"]].append(r)
    return by_task


def headline(payload):
    rs = payload["results"]
    n = len(rs) or 1
    expert = [0, 0]
    for r in rs:
        for tag, t in r["tags"].items():
            if tag != "fuzz":
                expert[0] += t["passed"]
                expert[1] += t["total"]
    return {
        "solve_rate": sum(r["solved"] for r in rs) / n,
        "case_accuracy": sum(r["case_accuracy"] for r in rs) / n,
        "expert_case_accuracy": expert[0] / expert[1] if expert[1] else None,
    }


def render_summary(payload, tasks):
    meta = {t.id: t for t in tasks}
    h = headline(payload)
    lines = [
        f"# Results: `{payload['model']}`",
        "",
        f"{payload['created']} · {len(payload['tasks'])} tasks × {payload['samples']} sample(s)",
        "",
        f"- **Solve rate (all cases pass): {h['solve_rate']:.1%}**",
        f"- Mean case accuracy: {h['case_accuracy']:.1%}",
    ]
    if h["expert_case_accuracy"] is not None:
        lines.append(f"- Accuracy on hand-written trap cases (excludes fuzz): {h['expert_case_accuracy']:.1%}")
    lines += ["", "| Task | Solved | Case accuracy | Traps failed (samples failing / samples) |", "|---|---|---|---|"]
    by_task = _agg(payload["results"])
    for task_id in payload["tasks"]:
        rs = by_task[task_id]
        solved = sum(r["solved"] for r in rs)
        acc = sum(r["case_accuracy"] for r in rs) / len(rs)
        tag_fail = defaultdict(int)
        statuses = defaultdict(int)
        for r in rs:
            if r["status"] != "ok":
                statuses[r["status"]] += 1
            for tag, t in r["tags"].items():
                if t["passed"] < t["total"]:
                    tag_fail[tag] += 1
        notes = [f"`{tag}` {c}/{len(rs)}" for tag, c in sorted(tag_fail.items(), key=lambda x: -x[1])]
        notes += [f"**{s}** {c}/{len(rs)}" for s, c in statuses.items()]
        lines.append(f"| {task_id} | {solved}/{len(rs)} | {acc:.1%} | {', '.join(notes) or '-'} |")

    lines += ["", "## Failure examples", ""]
    for task_id in payload["tasks"]:
        shown = 0
        for r in by_task[task_id]:
            if r["status"] not in ("ok",):
                lines.append(f"- **{task_id}** s{r['sample']}: {r['status']} "
                             f"{'; '.join(r.get('violations') or []) or (r.get('error') or '')[:200]}")
                continue
            for f in r["failed"]:
                if shown >= 3:
                    break
                got = f"got `{json.dumps(f['got'], ensure_ascii=False)}`" if "got" in f else f"raised `{f.get('error')}`"
                note = f" — {f['note']}" if "note" in f else ""
                lines.append(f"- **{task_id}** [{f['tag']}] `{task_id_args(f['args'])}` → expected "
                             f"`{json.dumps(f['expected'], ensure_ascii=False)}`, {got}{note}")
                shown += 1
    if len(lines) and lines[-1] == "":
        lines.append("No failures.")
    return "\n".join(lines) + "\n"


def task_id_args(args):
    return ", ".join(json.dumps(a, ensure_ascii=False) for a in args)


def render_comparison(payloads):
    task_ids = []
    for p in payloads:
        task_ids += [t for t in p["tasks"] if t not in task_ids]
    header = "| Task | " + " | ".join(f"`{p['model']}`" for p in payloads) + " |"
    lines = ["# Model comparison", "", "Cells: tasks solved / samples (mean case accuracy).", "",
             header, "|---|" + "---|" * len(payloads)]
    for tid in task_ids:
        row = [tid]
        for p in payloads:
            rs = [r for r in p["results"] if r["task"] == tid]
            if not rs:
                row.append("-")
                continue
            acc = sum(r["case_accuracy"] for r in rs) / len(rs)
            row.append(f"{sum(r['solved'] for r in rs)}/{len(rs)} ({acc:.0%})")
        lines.append("| " + " | ".join(row) + " |")
    row = ["**Solve rate**"] + [f"**{headline(p)['solve_rate']:.1%}**" for p in payloads]
    lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines) + "\n"
