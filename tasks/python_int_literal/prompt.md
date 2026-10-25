Write a Python function `is_valid_int_literal(s: str) -> bool` that returns `True` if and only if the whole string `s` is a valid **integer literal token** according to the Python 3.12 lexical grammar (the `integer` production in the language reference, section "Integer literals").

The string must be exactly one integer literal: no sign, no surrounding or embedded whitespace, no imaginary suffix, no floats. Do not evaluate or compile the string, and do not use `tokenize`, `ast`, `compile`, `eval` or `exec`.
