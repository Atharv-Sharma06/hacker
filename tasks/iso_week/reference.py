def _is_leap(y):
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def _ordinal(y, m, d):
    # days since 0001-01-01 (proleptic Gregorian), Monday == 0
    cum = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    py = y - 1
    days = py * 365 + py // 4 - py // 100 + py // 400 + cum[m - 1] + d - 1
    if m > 2 and _is_leap(y):
        days += 1
    return days


def _week1_monday(y):
    jan4 = _ordinal(y, 1, 4)
    return jan4 - jan4 % 7


def iso_week(year: int, month: int, day: int) -> list:
    o = _ordinal(year, month, day)
    iso_year = year
    start = _week1_monday(year)
    if o < start:
        iso_year -= 1
        start = _week1_monday(iso_year)
    else:
        nxt = _week1_monday(year + 1)
        if o >= nxt:
            iso_year += 1
            start = nxt
    return [iso_year, (o - start) // 7 + 1]
