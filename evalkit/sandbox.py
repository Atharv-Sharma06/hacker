"""Run candidate code against a task's cases in a separate, resource-limited process.

This is process isolation, not a security boundary. Run untrusted model output
inside a container or VM (see README).
"""

import json
import os
import pathlib
import subprocess
import sys
import tempfile

CHILD = pathlib.Path(__file__).resolve().parent / "_child.py"
TOTAL_TIMEOUT = 120
MEMORY_BYTES = 2 * 1024 ** 3


def _limits():
    try:
        import resource

        resource.setrlimit(resource.RLIMIT_AS, (MEMORY_BYTES, MEMORY_BYTES))
        resource.setrlimit(resource.RLIMIT_CPU, (TOTAL_TIMEOUT, TOTAL_TIMEOUT))
        resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    except (ImportError, ValueError, OSError):
        pass


def run_cases(code: str, task) -> dict:
    """Returns {"load_error": str|None, "cases": [{"id", "passed", ...}]}."""
    with tempfile.TemporaryDirectory(prefix="evalkit-") as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "candidate.py").write_text(code)
        out = tmp / "out.json"
        cmd = [sys.executable, "-I", str(CHILD), str(tmp / "candidate.py"),
               str(task.path / "cases.json"), task.function, str(out)]
        try:
            proc = subprocess.run(
                cmd, cwd=tmp, capture_output=True, text=True, timeout=TOTAL_TIMEOUT,
                preexec_fn=_limits if os.name == "posix" else None,
                env={"PATH": os.environ.get("PATH", ""), "PYTHONHASHSEED": "0"},
            )
        except subprocess.TimeoutExpired:
            return {"load_error": f"candidate exceeded {TOTAL_TIMEOUT}s in total", "cases": []}
        if not out.exists():
            return {"load_error": f"candidate crashed the interpreter (exit {proc.returncode}): "
                                  f"{proc.stderr[-1500:]}", "cases": []}
        return json.loads(out.read_text())
