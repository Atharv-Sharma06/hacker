"""Static checks run on a candidate before it is executed."""

import ast

_DYNAMIC_NAMES = {"__import__", "exec", "eval", "compile"}  # builtins called by bare name
_DYNAMIC_ATTRS = {"__import__", "import_module"}  # e.g. importlib.import_module; re.compile is fine


def check(code: str, forbidden: list) -> list:
    """Return a list of violations (empty when the code is acceptable)."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [f"syntax error: {e.msg} (line {e.lineno})"]
    banned = set(forbidden)
    problems = []

    def hit(name):
        return name.split(".")[0] in banned

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            problems += [f"forbidden import: {a.name}" for a in node.names if hit(a.name)]
        elif isinstance(node, ast.ImportFrom) and node.module and hit(node.module):
            problems.append(f"forbidden import: {node.module}")
        elif isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Name) and fn.id in _DYNAMIC_NAMES:
                problems.append(f"dynamic code/import not allowed: {fn.id}()")
            elif isinstance(fn, ast.Attribute) and fn.attr in _DYNAMIC_ATTRS:
                problems.append(f"dynamic code/import not allowed: {fn.attr}()")
    return problems
