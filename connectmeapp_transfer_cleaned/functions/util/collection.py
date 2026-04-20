

def clean(val):
    return val if val not in ("", [], {}, None) else None