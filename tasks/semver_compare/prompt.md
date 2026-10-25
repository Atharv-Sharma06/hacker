Write a Python function `compare(a: str, b: str) -> int` that compares two version strings by **Semantic Versioning 2.0.0 precedence** (semver.org, section 11).

Return `-1` if `a` has lower precedence than `b`, `0` if they have equal precedence, `1` if higher.

Both inputs are always valid SemVer 2.0.0 versions: `MAJOR.MINOR.PATCH`, optionally followed by `-` and a dot-separated pre-release, optionally followed by `+` and dot-separated build metadata. Numbers may be arbitrarily large.

Follow the specification exactly, including every rule about pre-release identifiers and build metadata.
