Write a Python function `iso_week(year: int, month: int, day: int) -> list[int]` that returns `[iso_year, iso_week_number]` for a date in the proleptic Gregorian calendar, per ISO 8601 week dates: weeks start on Monday, and week 1 of an ISO year is the week containing that year's first Thursday.

The input is always a valid date with `1 <= year <= 9999`. You may not import `datetime`, `calendar`, `time` or any date library; do the arithmetic yourself.

Return a two-element list, for example `iso_week(2021, 1, 3) == [2020, 53]`.
