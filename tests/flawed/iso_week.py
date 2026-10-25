# Typical mistake: week = (day_of_year + weekday offset) // 7 + 1, no year rollover.
def iso_week(year, month, day):
    cum = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    doy = cum[month - 1] + day + (1 if leap and month > 2 else 0)
    y = year - 1
    jan1 = (y * 365 + y // 4 - y // 100 + y // 400) % 7  # Monday == 0
    return [year, (doy - 1 + jan1) // 7 + 1]
