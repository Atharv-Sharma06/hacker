Write a Python function `parse_csv(text: str) -> list[list[str]]` that parses CSV text into a list of records, each a list of field strings. Do **not** use the `csv` module or any third-party library.

Grammar (delimiter `,`, quote `"`):

- The input is a sequence of records. Each record is terminated by a line break (`\r\n` or `\n`), except that the **last** record's line break is optional. So `"a\n"` is one record and `"a\n\n"` is two records (`[["a"], [""]]`).
- An empty input `""` has zero records and returns `[]`.
- A record is one or more fields separated by `,`. An empty line is a record with one empty field.
- An **unquoted** field is any run of characters other than `,`, `\n` and the two-character sequence `\r\n`. A `"` appearing inside an unquoted field (not at its first character) is an ordinary character. A lone `\r` not followed by `\n` is an ordinary character.
- A **quoted** field starts with `"` as its first character and ends at the matching closing `"`. Inside it, `""` stands for one `"` character, and `,`, `\r` and `\n` are ordinary characters kept verbatim.
- After a closing quote, the next character must be `,`, a line break, or the end of input. Anything else is malformed: raise `ValueError`.
- A quoted field that never closes is malformed: raise `ValueError`.

Field values are returned exactly as written (no whitespace trimming, no type conversion).
