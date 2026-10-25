"""Model adapters. Each one turns (system, prompt) into a text response.

Spec strings accepted by --model:
  reference               the task's reference solution (sanity check: must score 100%)
  anthropic:<model-id>    Claude via the official `anthropic` SDK (pip install anthropic)
  cmd:<shell command>     any model behind a CLI: prompt on stdin, response on stdout
  dir:<path>              pre-recorded responses, <path>/<task_id>.md (or _s<k>.md per sample)
"""

import os
import pathlib
import shlex
import subprocess


class Model:
    name = "model"

    def generate(self, system: str, prompt: str, task, sample: int) -> str:
        raise NotImplementedError


class ReferenceModel(Model):
    name = "reference"

    def generate(self, system, prompt, task, sample):
        return "```python\n" + task.reference_path.read_text() + "```\n"


class AnthropicModel(Model):
    def __init__(self, model_id, effort=None, max_tokens=64000):
        import anthropic  # imported lazily so the rest of the kit needs no third-party packages

        self.client = anthropic.Anthropic()
        self.model_id = model_id
        self.effort = effort
        self.max_tokens = max_tokens
        self.name = f"anthropic:{model_id}" + (f"@{effort}" if effort else "")

    def generate(self, system, prompt, task, sample):
        kwargs = dict(
            model=self.model_id,
            max_tokens=self.max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        if self.effort:
            kwargs["output_config"] = {"effort": self.effort}
        # Server-side refusal fallbacks are deliberately NOT enabled: a fallback
        # would silently score a different model than the one being measured.
        with self.client.messages.stream(**kwargs) as stream:
            message = stream.get_final_message()
        if message.stop_reason == "refusal":
            raise RuntimeError(f"model refused: {getattr(message, 'stop_details', None)}")
        text = "".join(block.text for block in message.content if block.type == "text")
        if message.stop_reason == "max_tokens":
            text += "\n<!-- evalkit: response truncated at max_tokens -->"
        return text


class CommandModel(Model):
    def __init__(self, command):
        self.command = command
        self.name = f"cmd:{shlex.split(command)[0]}"

    def generate(self, system, prompt, task, sample):
        proc = subprocess.run(
            self.command, shell=True, input=f"{system}\n\n{prompt}", capture_output=True,
            text=True, timeout=1800, env={**os.environ, "EVALKIT_TASK": task.id, "EVALKIT_SAMPLE": str(sample)},
        )
        if proc.returncode != 0:
            raise RuntimeError(f"command failed ({proc.returncode}): {proc.stderr[-500:]}")
        return proc.stdout


class DirModel(Model):
    def __init__(self, path):
        self.path = pathlib.Path(path)
        self.name = f"dir:{self.path.name}"

    def generate(self, system, prompt, task, sample):
        for candidate in (self.path / f"{task.id}_s{sample}.md", self.path / f"{task.id}.md"):
            if candidate.exists():
                return candidate.read_text()
        raise FileNotFoundError(f"no recorded response for {task.id} in {self.path}")


def make_model(spec: str, effort: str | None = None) -> Model:
    kind, _, arg = spec.partition(":")
    if kind == "reference":
        return ReferenceModel()
    if kind == "anthropic" and arg:
        return AnthropicModel(arg, effort=effort)
    if kind == "cmd" and arg:
        return CommandModel(arg)
    if kind == "dir" and arg:
        return DirModel(arg)
    raise SystemExit(f"unrecognised --model {spec!r}; see `python -m evalkit run --help`")
