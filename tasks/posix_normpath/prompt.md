Write a Python function `normpath(path: str) -> str` that normalizes a POSIX path **lexically** (never touching the filesystem). It must return exactly what CPython's `posixpath.normpath` returns for every input string, but you may **not** import `os`, `posixpath`, `pathlib` or any path library.

The rules:

- `""` normalizes to `"."`.
- Repeated separators collapse, and `.` components are removed.
- A `..` component removes the preceding component, unless that component is itself `..`.
- In an absolute path, a `..` that would go above the root is dropped. In a relative path, leading `..` components are kept.
- A trailing slash is removed (except when the result is a root).
- If the result would be empty, return `"."`.
- Leading slashes: POSIX allows a path beginning with exactly two slashes to be interpreted in an implementation-defined way, so exactly two leading slashes are preserved as `//`. One leading slash, or three or more, become a single `/`.

Components are any other non-empty strings and are kept as-is (they may contain spaces, dots such as `...`, or any Unicode).
