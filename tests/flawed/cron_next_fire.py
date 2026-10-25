# Typical mistake: AND the day-of-month and day-of-week fields.
import datetime as dt

def _f(t, lo, hi):
    s = set()
    for it in t.split(","):
        st = 1
        if "/" in it:
            it, st = it.split("/"); st = int(st)
            if it != "*" and "-" not in it:
                it = f"{it}-{hi}"
        a, z = (lo, hi) if it == "*" else map(int, it.split("-")) if "-" in it else (int(it), int(it))
        s |= set(range(a, z + 1, st))
    return s

def next_fire(expr, now):
    f = expr.split()
    mi, ho, dm, mo, dw = (_f(x, *r) for x, r in zip(f, [(0, 59), (0, 23), (1, 31), (1, 12), (0, 7)]))
    dw = {d % 7 for d in dw}
    t = dt.datetime.strptime(now, "%Y-%m-%dT%H:%M")
    end = dt.datetime(t.year + 10, 12, 31, 23, 59)
    day = t.date()
    while dt.datetime.combine(day, dt.time()) <= end:
        if day.month in mo and day.day in dm and (day.isoweekday() % 7) in dw:
            for h in sorted(ho):
                for m in sorted(mi):
                    c = dt.datetime.combine(day, dt.time(h, m))
                    if c > t:
                        return c.strftime("%Y-%m-%dT%H:%M")
        day += dt.timedelta(days=1)
    return None
