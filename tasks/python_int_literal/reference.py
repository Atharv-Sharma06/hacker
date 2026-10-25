import re

_DIG = {"b": "[01]", "o": "[0-7]", "x": "[0-9a-fA-F]"}
_PATTERN = re.compile(
    r"(?:[1-9](?:_?[0-9])*"
    r"|0+(?:_?0)*"
    r"|0[bB](?:_?[01])+"
    r"|0[oO](?:_?[0-7])+"
    r"|0[xX](?:_?[0-9a-fA-F])+)",
    re.ASCII,
)


def is_valid_int_literal(s: str) -> bool:
    return _PATTERN.fullmatch(s) is not None
