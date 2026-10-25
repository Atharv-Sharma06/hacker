# Edge-Case Eval: can frontier models implement a spec *exactly*?

An eval for the **micro1 Eval Hackathon**, in the software engineering domain.

Frontier models are good at writing code that looks right and handles the common case. Production software breaks on the cases the spec spells out and the model skims past: a SemVer build tag with a hyphen in it, a CSV blank line, `//` at the start of a POSIX path, `2.675` stored as a binary float, the Vixie-cron rule that ORs the two day fields together. This eval measures that gap. Every task is a short, unambiguous spec for a small function, graded by running the code against hundreds of cases. A task counts as solved only if **every** case passes, because "correct except on the edge cases" is exactly the failure being measured.

- **Fully deterministic grading.** No LLM judge. The model's code runs in a separate process and its outputs are compared exactly, types included.
- **The answer key is checked two ways.** Hand-written trap cases carry an expected value that I wrote by hand, and the reference must agree. Fuzz cases are cross-checked against an independent oracle: CPython's own stdlib where one exists (`posixpath.normpath`, `csv`, `decimal`, `date.isocalendar`, the `ast` parser), otherwise a second, deliberately naive implementation (minute-by-minute brute force for cron). Any disagreement aborts the build.
- **Each trap is shown to bite.** `tests/flawed/` holds one plausible wrong solution per task, written to make the most common mistake. The test suite asserts that each one is caught by the trap it targets.
- **Results say *why* a model failed.** Cases are tagged by trap, so the summary reports "failed `dom-dow-or` in 3/5 samples" rather than just a score.

## Tasks

| Task | Function | Cases | What it tests | The trap |
|---|---|---|---|---|
| `semver_compare` | `compare(a, b)` | 203 | SemVer 2.0.0 §11 precedence | `0A` is alphanumeric; `alpha.10 > alpha.9`; build metadata ignored even when it contains `-` |
| `csv_parse` | `parse_csv(text)` | 152 | strict RFC 4180-style parser, no `csv` module | quoted CR/LF kept, blank records, bare `"` is literal, text after a closing quote is an error |
| `posix_normpath` | `normpath(path)` | 145 | `posixpath.normpath` without `os` | exactly two leading slashes are preserved; `..` above `/` dropped |
| `decimal_round_half_even` | `round_half_even(value, places)` | 181 | exact banker's rounding of decimal strings | `float("2.675")` is below the tie; carries; `-0.00` |
| `cron_next_fire` | `next_fire(expr, now)` | 93 | next fire time, Vixie cron semantics | day-of-month **OR** day-of-week when both are restricted; `*/2` counts as `*`; impossible dates return `None` |
| `python_int_literal` | `is_valid_int_literal(s)` | 200 | Python 3 lexical grammar | `int(s, 0)` accepts `" 1"`, `"-1"`, `"١"`; `00` is valid but `01` is not; `0x_f` is valid |
| `iso_week` | `iso_week(y, m, d)` | 136 | ISO 8601 week dates without `datetime` | late December in week 1 of next year, early January in week 52/53 of last year |

Each task lives in `tasks/<id>/`:

```
prompt.md       the spec the model sees
task.json       function name, forbidden imports, the traps it targets
reference.py    reference solution
cases.json      generated test cases (args, expected value, trap tag, optional note)
```

The prompts state every rule a case depends on. If a model fails, it is because it did not follow a rule it was given, not because the rule was hidden.

## Running it

Python 3.11+ only. The harness uses no third-party packages.

```sh
python -m evalkit list                                      # tasks and case counts
python -m evalkit run --model reference                     # sanity check: must score 100%
python -m unittest -v tests.test_evalkit                    # reference passes, every flawed solution is caught
```

Evaluate a model:

```sh
pip install anthropic                    # only for the anthropic: adapter
export ANTHROPIC_API_KEY=...
python -m evalkit run --model anthropic:claude-opus-5-5 --effort high --samples 5

# Any other model or agent: a command that reads the prompt on stdin and prints the response
python -m evalkit run --model "cmd:my-model-cli --flag" --samples 5

# Responses you already collected, as <dir>/<task_id>.md or <task_id>_s<k>.md
python -m evalkit run --model dir:path/to/responses

# Side-by-side table
python -m evalkit compare results/anthropic_claude-opus-5-5@high results/other-model
```

Each run writes `results/<model>/`:

- `responses/<task>_s<k>.md` the raw model output. Runs resume: an existing response is graded again, never regenerated.
- `results.json` every case failure with arguments, expected value, the model's output, and the trap tag.
- `summary.md` headline numbers, a per-task table of which traps failed, and failure examples.

Grade one response by hand: `python -m evalkit grade csv_parse response.md`.

### Metrics

- **Solve rate**: fraction of (task, sample) pairs where every case passes. This is the headline number.
- **Case accuracy**: fraction of cases passed, averaged. It shows how close a model got; a model can score 87% of cases and still be wrong on the one rule that matters.
- **Trap-case accuracy**: accuracy on the hand-written cases only, excluding fuzz.
- **Per-trap failure counts** in `summary.md`.

### Statuses

`ok`; `no_code` (no code block found); `syntax_error`; `policy_violation` (imported a forbidden module such as `csv` or `decimal`, or used `eval`/`exec`/`__import__`); `load_error` (crashed on import or killed the interpreter); `generation_error` (the API call failed or the model refused). Every non-`ok` status counts as unsolved.

## How the answer key is built

```sh
python scripts/build_cases.py
```

The script is deterministic (fixed seed) and CI checks that `cases.json` matches its output. For each task it:

1. runs the hand-written trap cases through `reference.py` and aborts if any hand-written expectation disagrees;
2. generates random inputs, focused on the risky region (year boundaries, exact ties, `..` chains, quoted line breaks), and aborts if the reference disagrees with the independent oracle;
3. writes the cases with the reference's outputs.

Fuzz for `csv_parse` is limited to inputs where the stdlib `csv` module and this grammar agree (no blank records, no lone CR). The cases outside that subset are hand-written.

## Sandbox

Candidate code runs in a fresh `python -I` process with a scrubbed environment, a temp working directory, memory, CPU-time and open-file limits, a 5-second per-case alarm and a 120-second total timeout. Its stdout is redirected so printing cannot corrupt the results. **This is process isolation, not a security boundary.** Run untrusted model output inside a container or VM.

## Adding a task

1. Create `tasks/<id>/` with `prompt.md`, `task.json` and `reference.py`.
2. Add a `build_<id>` function to `scripts/build_cases.py` with hand-written trap cases and, wherever possible, an independent oracle for fuzzing.
3. Add a plausible wrong solution to `tests/flawed/<id>.py` and its trap to `EXPECTED_TRAP` in the tests.
4. `python scripts/build_cases.py && python -m unittest tests.test_evalkit`.

## Limitations

- Seven tasks is a small suite. Per-task solve rates over 5+ samples are more meaningful than one overall number.
- These are single-turn, single-function tasks. They measure whether a model follows a precise spec on the first attempt, not whether it would catch the bug with tests or tools.
- The specs are public once this repo is, so later models may have seen them. The build script makes it cheap to change seeds or add fresh hand-written cases.

## Submission

`scripts/package_submission.sh` builds `submission.zip` from the tracked files plus `results/` (code only, no videos).
