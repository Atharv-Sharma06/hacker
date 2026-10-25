def compare(a: str, b: str) -> int:
    def parse(v):
        core, _, _build = v.partition("+")
        core, _, pre = core.partition("-")
        major, minor, patch = (int(x) for x in core.split("."))
        return (major, minor, patch), (pre.split(".") if pre else [])

    def cmp_ident(x, y):
        xn, yn = x.isdigit(), y.isdigit()
        if xn and yn:
            return (int(x) > int(y)) - (int(x) < int(y))
        if xn != yn:
            return -1 if xn else 1
        return (x > y) - (x < y)

    (ca, pa), (cb, pb) = parse(a), parse(b)
    if ca != cb:
        return -1 if ca < cb else 1
    if not pa or not pb:
        return (not pa) - (not pb) if pa or pb else 0
    for x, y in zip(pa, pb):
        c = cmp_ident(x, y)
        if c:
            return c
    return (len(pa) > len(pb)) - (len(pa) < len(pb))
