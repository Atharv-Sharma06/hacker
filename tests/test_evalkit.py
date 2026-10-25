import pathlib
import unittest

from evalkit import policy
from evalkit.extract import extract_code
from evalkit.grading import grade
from evalkit.tasks import load_tasks

FLAWED = pathlib.Path(__file__).parent / "flawed"

# The trap each deliberately flawed solution must be caught by.
EXPECTED_TRAP = {
    "semver_compare": "build-with-hyphen",
    "csv_parse": "quoted-newline",
    "posix_normpath": "double-slash-root",
    "decimal_round_half_even": "float-trap",
    "cron_next_fire": "dom-dow-or",
    "python_int_literal": "int()-accepts-but-grammar-rejects",
    "iso_week": "year-boundary",
}


def fenced(code):
    return f"Here you go:\n```python\n{code}\n```\n"


class TestTasks(unittest.TestCase):
    def test_every_task_has_a_flawed_fixture(self):
        self.assertEqual({t.id for t in load_tasks()}, set(EXPECTED_TRAP))

    def test_reference_solutions_pass_every_case(self):
        for task in load_tasks():
            with self.subTest(task=task.id):
                result = grade(task, fenced(task.reference_path.read_text()))
                self.assertEqual(result["status"], "ok", result)
                self.assertTrue(result["solved"], result["failed"][:3])

    def test_flawed_solutions_are_caught_by_their_trap(self):
        for task in load_tasks():
            with self.subTest(task=task.id):
                result = grade(task, fenced((FLAWED / f"{task.id}.py").read_text()))
                self.assertFalse(result["solved"])
                self.assertIn(EXPECTED_TRAP[task.id], {f["tag"] for f in result["failed"]})

    def test_case_ids_unique_and_expectations_present(self):
        for task in load_tasks():
            ids = [c["id"] for c in task.cases]
            self.assertEqual(len(ids), len(set(ids)), task.id)
            for c in task.cases:
                self.assertTrue(("expected" in c) ^ ("expected_error" in c), c)


class TestHarness(unittest.TestCase):
    def setUp(self):
        (self.task,) = load_tasks(["python_int_literal"])

    def test_forbidden_import_is_rejected(self):
        code = "import tokenize\ndef is_valid_int_literal(s):\n    return True\n"
        self.assertEqual(grade(self.task, fenced(code))["status"], "policy_violation")
        self.assertTrue(policy.check("from ast import parse", ["ast"]))
        self.assertTrue(policy.check("x = eval('1')", []))
        self.assertFalse(policy.check("import re\nP = re.compile('a')", ["ast"]))

    def test_extract_prefers_block_defining_function(self):
        resp = "```python\nprint(1)\n```\n```python\ndef f(x):\n    return x\n```\n```python\nf(1)\n```"
        self.assertIn("def f", extract_code(resp, "f"))
        self.assertIsNone(extract_code("no code here", "f"))

    def test_no_code(self):
        self.assertEqual(grade(self.task, "I cannot do that.")["status"], "no_code")

    def test_crash_and_syntax_error_are_contained(self):
        crash = "import os\ndef is_valid_int_literal(s):\n    os._exit(3)\n"
        self.assertEqual(grade(self.task, fenced(crash))["status"], "load_error")
        self.assertEqual(grade(self.task, fenced("def is_valid_int_literal(s:\n"))["status"], "syntax_error")

    def test_candidate_stdout_does_not_corrupt_results(self):
        (task,) = load_tasks(["semver_compare"])
        code = task.reference_path.read_text().replace(
            "def compare(a: str, b: str) -> int:\n", "def compare(a: str, b: str) -> int:\n    print('noise')\n")
        self.assertTrue(grade(task, fenced(code))["solved"])

    def test_wrong_type_is_a_failure(self):
        code = "def is_valid_int_literal(s):\n    return 1 if s == '0' else 0\n"
        self.assertEqual(grade(self.task, fenced(code))["case_accuracy"], 0.0)


if __name__ == "__main__":
    unittest.main()
