Write a Python function `round_half_even(value: str, places: int) -> str` that rounds a decimal number, given as a string, to `places` digits after the decimal point using **round-half-to-even** (banker's rounding), treating the input as an **exact** decimal value.

Input: `value` matches the regex `-?[0-9]+(\.[0-9]+)?` (it may have leading zeros and any number of digits, far more than a float can hold). `places` is an integer, `0 <= places <= 30`.

Rounding: if the discarded part is more than half a unit in the last kept place, round away from zero; if less, round toward zero; if **exactly** half, round so that the last kept digit is even.

Output format:

- No leading zeros in the integer part, except a single `0` when it is zero.
- If `places > 0`, a `.` followed by exactly `places` digits (pad with zeros if needed). If `places == 0`, no decimal point.
- A leading `-` only if the rounded result is non-zero. A result of zero is never negative (`"-0.001"` at 2 places is `"0.00"`).

You may not import `decimal`, `fractions`, `numpy` or any arbitrary-precision library.
