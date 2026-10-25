# Typical mistake: binary floats.
def round_half_even(value, places):
    r = round(float(value), places)
    s = f"{r:.{places}f}"
    return s[1:] if s.startswith("-") and float(s) == 0 else s
