import re

_FENCE = re.compile(r"```[ \t]*(?:python|py|python3)?[ \t]*\n(.*?)```", re.DOTALL | re.IGNORECASE)


def extract_code(response: str, function: str) -> str | None:
    """Return the code block that defines `function` (the last one if several do).

    Falls back to the last fenced block, then to the raw response if it looks
    like bare code. Returns None when nothing usable is found.
    """
    blocks = _FENCE.findall(response)
    defining = [b for b in blocks if re.search(rf"^\s*def\s+{re.escape(function)}\s*\(", b, re.MULTILINE)]
    if defining:
        return defining[-1]
    if blocks:
        return blocks[-1]
    if re.search(rf"^def\s+{re.escape(function)}\s*\(", response, re.MULTILINE):
        return response
    return None
