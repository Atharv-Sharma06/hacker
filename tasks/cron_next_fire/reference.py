import datetime as _dt

_RANGES = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 7)]


def _parse_field(text, lo, hi):
    allowed = set()
    for part in text.split(","):
        base, _, step = part.partition("/")
        step = int(step) if step else 1
        if base == "*":
            start, end = lo, hi
        elif "-" in base:
            a, b = base.split("-")
            start, end = int(a), int(b)
        else:
            start = int(base)
            end = hi if step != 1 or "/" in part else start
        allowed.update(range(start, end + 1, step))
    return allowed


def next_fire(expr: str, now: str):
    fields = expr.split()
    minute, hour, dom, month, dow = (
        _parse_field(f, lo, hi) for f, (lo, hi) in zip(fields, _RANGES)
    )
    if 7 in dow:
        dow.add(0)
    dom_star = fields[2].startswith("*")
    dow_star = fields[4].startswith("*")

    def day_ok(d):
        if d.month not in month:
            return False
        dm = d.day in dom
        dw = (d.isoweekday() % 7) in dow
        if dom_star or dow_star:
            return dm and dw
        return dm or dw

    current = _dt.datetime.strptime(now, "%Y-%m-%dT%H:%M")
    start = current + _dt.timedelta(minutes=1)
    last_day = _dt.date(current.year + 10, 12, 31)
    day = start.date()
    first = True
    while day <= last_day:
        if day_ok(day):
            for h in sorted(hour):
                if first and h < start.hour:
                    continue
                for m in sorted(minute):
                    if first and h == start.hour and m < start.minute:
                        continue
                    return f"{day.isoformat()}T{h:02d}:{m:02d}"
        day += _dt.timedelta(days=1)
        first = False
    return None
