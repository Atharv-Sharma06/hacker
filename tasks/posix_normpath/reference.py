def normpath(path: str) -> str:
    if path == "":
        return "."
    if path.startswith("/"):
        prefix = "//" if path.startswith("//") and not path.startswith("///") else "/"
    else:
        prefix = ""
    out = []
    for comp in path.split("/"):
        if comp in ("", "."):
            continue
        if comp == "..":
            if out and out[-1] != "..":
                out.pop()
            elif not prefix:
                out.append("..")
            continue
        out.append(comp)
    return (prefix + "/".join(out)) or "."
