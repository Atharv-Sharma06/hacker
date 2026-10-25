# Typical mistake: trust int(s, 0).
def is_valid_int_literal(s):
    try:
        int(s, 0)
        return True
    except ValueError:
        return False
