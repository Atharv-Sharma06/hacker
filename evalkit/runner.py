import concurrent.futures as cf
import datetime as dt
import json
import pathlib
import time
import traceback

from .grading import grade
from .report import render_summary
from .tasks import SYSTEM_PROMPT


def run(model, tasks, samples: int, out_dir: pathlib.Path, workers: int = 4) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "responses").mkdir(exist_ok=True)
    jobs = [(t, k) for t in tasks for k in range(samples)]

    def one(job):
        task, k = job
        path = out_dir / "responses" / f"{task.id}_s{k}.md"
        started = time.time()
        if path.exists():  # resume: never pay for the same generation twice
            response = path.read_text()
        else:
            try:
                response = model.generate(SYSTEM_PROMPT, task.prompt, task, k)
            except Exception as e:  # recorded as a failed sample, not a crash of the whole run
                return {"task": task.id, "sample": k, "solved": False, "case_accuracy": 0.0,
                        "status": "generation_error", "error": f"{type(e).__name__}: {e}",
                        "trace": traceback.format_exc(limit=2), "failed": [], "tags": {}, "violations": []}
            path.write_text(response)
        graded = grade(task, response)
        graded.update(sample=k, seconds=round(time.time() - started, 1))
        mark = "PASS" if graded["solved"] else graded["status"].upper() if graded["status"] != "ok" else "FAIL"
        print(f"  {task.id:26s} s{k}  {mark:17s} {graded['case_accuracy']:6.1%}", flush=True)
        return graded

    with cf.ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(one, jobs))

    payload = {
        "model": model.name,
        "created": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "samples": samples,
        "tasks": [t.id for t in tasks],
        "results": sorted(results, key=lambda r: (r["task"], r["sample"])),
    }
    (out_dir / "results.json").write_text(json.dumps(payload, indent=1, ensure_ascii=False))
    (out_dir / "summary.md").write_text(render_summary(payload, tasks))
    return payload
