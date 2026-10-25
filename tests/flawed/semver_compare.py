# Typical mistake: split on '-' before '+', and treat any digit-leading id as numeric.
def compare(a, b):
    def key(v):
        core, _, pre = v.partition("-")
        core = core.split("+")[0]
        pre = pre.split("+")[0]
        nums = tuple(int(x) for x in core.split("."))
        ids = []
        for p in pre.split(".") if pre else []:
            ids.append((0, int(p), "") if p[0].isdigit() and p.isalnum() and p[:1].isdigit() and p.isdigit() else (1, 0, p))
        return nums, (1,) if not pre else (0, *ids)
    ka, kb = key(a), key(b)
    return (ka > kb) - (ka < kb)
