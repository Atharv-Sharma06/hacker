# Typical mistake: forgets the '//' rule.
def normpath(path):
    if not path:
        return "."
    absolute = path.startswith("/")
    out = []
    for c in path.split("/"):
        if c in ("", "."):
            continue
        if c == "..":
            if out and out[-1] != "..":
                out.pop()
            elif not absolute:
                out.append("..")
        else:
            out.append(c)
    return ("/" if absolute else "") + "/".join(out) or "."
