from typing import List, Dict

# Very simple availability mock: accept list of user ids and a date range
# and return them as "available". Replace with real logic later.

def find_available(users: List[str], start: str, end: str) -> List[Dict]:
    return [{"user_id": u, "available": True, "start": start, "end": end} for u in users]
