import json
import pathlib
from dataclasses import dataclass, field

TASKS_DIR = pathlib.Path(__file__).resolve().parent.parent / "tasks"

SYSTEM_PROMPT = (
    "You are being evaluated on writing correct Python 3.12 code from a precise specification. "
    "Reply with exactly one ```python fenced code block containing the complete implementation "
    "(standard library only, unless the task forbids specific modules). "
    "Do not include tests, examples, or a __main__ block."
)


@dataclass
class Task:
    id: str
    title: str
    function: str
    prompt: str
    forbidden_imports: list
    cases: list
    traps: list = field(default_factory=list)
    skill: str = ""
    path: pathlib.Path = None

    @property
    def reference_path(self):
        return self.path / "reference.py"


def load_task(path):
    path = pathlib.Path(path)
    meta = json.loads((path / "task.json").read_text())
    return Task(
        id=meta["id"],
        title=meta["title"],
        function=meta["function"],
        prompt=(path / "prompt.md").read_text(),
        forbidden_imports=meta.get("forbidden_imports", []),
        cases=json.loads((path / "cases.json").read_text()),
        traps=meta.get("traps", []),
        skill=meta.get("skill", ""),
        path=path,
    )


def load_tasks(selected=None, tasks_dir=TASKS_DIR):
    tasks = [load_task(p) for p in sorted(pathlib.Path(tasks_dir).iterdir()) if (p / "task.json").exists()]
    if selected:
        wanted = set(selected)
        unknown = wanted - {t.id for t in tasks}
        if unknown:
            raise SystemExit(f"unknown task id(s): {', '.join(sorted(unknown))}")
        tasks = [t for t in tasks if t.id in wanted]
    return tasks
