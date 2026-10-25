def round_half_even(value: str, places: int) -> str:
    neg = value.startswith("-")
    body = value[1:] if neg else value
    int_part, _, frac = body.partition(".")
    digits = int_part + frac
    scale = len(frac)
    n = int(digits)  # exact magnitude * 10**scale
    if places >= scale:
        q = n * 10 ** (places - scale)
    else:
        q, r = divmod(n, 10 ** (scale - places))
        half = 5 * 10 ** (scale - places - 1)
        if r > half or (r == half and q % 2 == 1):
            q += 1
    s = str(q)
    if places:
        s = s.rjust(places + 1, "0")
        s = s[:-places] + "." + s[-places:]
    if neg and q != 0:
        s = "-" + s
    return s
