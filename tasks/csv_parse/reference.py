def parse_csv(text: str) -> list:
    records, record, field = [], [], []
    i, n = 0, len(text)
    if n == 0:
        return []
    while True:
        # start of a field
        if i < n and text[i] == '"':
            i += 1
            while True:
                if i >= n:
                    raise ValueError("unterminated quoted field")
                ch = text[i]
                if ch == '"':
                    if i + 1 < n and text[i + 1] == '"':
                        field.append('"')
                        i += 2
                        continue
                    i += 1
                    break
                field.append(ch)
                i += 1
            if i < n and text[i] not in ',\n' and text[i:i + 2] != '\r\n':
                raise ValueError("unexpected character after closing quote")
        else:
            while i < n and text[i] != ',' and text[i] != '\n' and text[i:i + 2] != '\r\n':
                field.append(text[i])
                i += 1
        record.append("".join(field))
        field = []
        if i >= n:
            records.append(record)
            return records
        if text[i] == ',':
            i += 1
            continue
        i += 2 if text[i] == '\r' else 1
        records.append(record)
        record = []
        if i >= n:
            return records
