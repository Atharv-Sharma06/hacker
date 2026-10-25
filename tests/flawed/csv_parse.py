# Typical mistake: splitlines() first, so quoted newlines break and blank records vanish.
def parse_csv(text):
    out = []
    for line in text.splitlines():
        fields, cur, q = [], "", False
        i = 0
        while i < len(line):
            c = line[i]
            if q:
                if c == '"' and line[i + 1:i + 2] == '"':
                    cur += '"'; i += 1
                elif c == '"':
                    q = False
                else:
                    cur += c
            elif c == '"':
                q = True
            elif c == ",":
                fields.append(cur); cur = ""
            else:
                cur += c
            i += 1
        fields.append(cur)
        out.append(fields)
    return out
