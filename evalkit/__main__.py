import argparse
import json
import pathlib
import re
import sys

from .models import make_model
from .report import render_comparison
from .runner import run
from .tasks import load_tasks


def main(argv=None):
    p = argparse.ArgumentParser(prog="python -m evalkit")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="generate and grade responses")
    r.add_argument("--model", required=True,
                   help="reference | anthropic:<model-id> | cmd:<shell command> | dir:<path>")
    r.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"],
                   help="Claude effort level (anthropic: models only)")
    r.add_argument("--tasks", nargs="*", help="task ids (default: all)")
    r.add_argument("--samples", type=int, default=1, help="independent samples per task")
    r.add_argument("--workers", type=int, default=4)
    r.add_argument("--out", help="output directory (default: results/<model>)")

    g = sub.add_parser("grade", help="grade one response file against one task")
    g.add_argument("task")
    g.add_argument("response", type=pathlib.Path)

    c = sub.add_parser("compare", help="side-by-side table of several result directories")
    c.add_argument("dirs", nargs="+", type=pathlib.Path)

    sub.add_parser("list", help="list tasks")

    a = p.parse_args(argv)
    if a.cmd == "list":
        for t in load_tasks():
            print(f"{t.id:26s} {len(t.cases):4d} cases  {t.title}")
    elif a.cmd == "run":
        model = make_model(a.model, a.effort)
        out = pathlib.Path(a.out or f"results/{re.sub(r'[^A-Za-z0-9_.@-]+', '_', model.name)}")
        tasks = load_tasks(a.tasks)
        print(f"{model.name}: {len(tasks)} tasks × {a.samples} sample(s) -> {out}")
        payload = run(model, tasks, a.samples, out, a.workers)
        print("\n" + (out / "summary.md").read_text())
        if a.model == "reference" and not all(r["solved"] for r in payload["results"]):
            sys.exit("reference solutions failed their own cases")
    elif a.cmd == "grade":
        from .grading import grade

        (task,) = load_tasks([a.task])
        print(json.dumps(grade(task, a.response.read_text()), indent=1, ensure_ascii=False))
    elif a.cmd == "compare":
        payloads = [json.loads((d / "results.json").read_text()) for d in a.dirs]
        print(render_comparison(payloads))


if __name__ == "__main__":
    main()
