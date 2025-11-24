def ensure_keys(data: dict, keys: list):
    missing = [k for k in keys if k not in data]
    if missing:
        return False, missing
    return True, []
