Write a Python function `next_fire(expr: str, now: str) -> str | None` that returns the first time **strictly after** `now` at which a cron expression fires, using the semantics of classic Vixie cron (the cron in most Linux distributions). You may not use `croniter` or any cron/scheduling library; the standard `datetime` module is allowed.

`now` and the result are naive local times formatted `YYYY-MM-DDTHH:MM` (no seconds, no time zones, no DST).

`expr` has exactly five space-separated fields: minute (0-59), hour (0-23), day of month (1-31), month (1-12), day of week (0-7, where both 0 and 7 mean Sunday, 1 is Monday). No names (`JAN`, `MON`), no `@` macros, no `L`, `W`, `#` or `?`.

Each field is a comma-separated list of items. Each item is one of:

- `*` (every value in the field's range)
- `N` (a single value)
- `A-B` (inclusive range)
- any of the above followed by `/S` (every S-th value starting at the item's start). For a single value, `N/S` means `N-max/S`, where max is the field's maximum.

Day matching follows Vixie cron exactly: if **both** the day-of-month field and the day-of-week field are restricted, a day matches when **either** field matches. If either of the two fields begins with the character `*` (this includes items such as `*/2`), it is treated as unrestricted for this rule, and a day matches only when **both** fields match. The month field must always match.

If the expression has no firing time on or before 23:59 on December 31 of the year `now.year + 10`, return `None`.

All inputs are well-formed.
