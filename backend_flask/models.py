from typing import Dict
from uuid import uuid4

# In-memory stores
USERS: Dict[str, Dict] = {}
EVENTS: Dict[str, Dict] = {}
AVAILABILITIES: Dict[str, Dict] = {}

def create_user(username: str, hashed_password: str, role: str = "employee") -> Dict:
    user_id = str(uuid4())
    user = {"id": user_id, "username": username, "password": hashed_password, "role": role}
    USERS[user_id] = user
    return user

def find_user_by_username(username: str):
    for u in USERS.values():
        if u["username"] == username:
            return u
    return None

def get_user_public(user: Dict) -> Dict:
    return {"id": user["id"], "username": user["username"], "role": user.get("role", "employee")}

def create_event(data: Dict) -> Dict:
    event_id = str(uuid4())
    # normalize fields: title/name, start/end, capacity, type, location, hours
    event = {
        "id": event_id,
        "title": data.get("title") or data.get("name"),
        "description": data.get("description", ""),
        "start": data.get("start"),
        "end": data.get("end"),
        "capacity": int(data.get("capacity", data.get("amount", 1))),
        "type": data.get("type", "general"),
        "location": data.get("location", ""),
        "hours": data.get("hours", ""),
        "assigned": data.get("assigned", []),
        "pending": data.get("pending", []),
    }
    EVENTS[event_id] = event
    return event

def list_events():
    return list(EVENTS.values())

def assign_user_to_event(event_id: str, user_id: str) -> bool:
    event = EVENTS.get(event_id)
    if not event:
        return False
    assigned = event.setdefault("assigned", [])
    if user_id in assigned:
        return True
    if len(assigned) >= int(event.get("capacity", 1)):
        return False
    assigned.append(user_id)
    # If user was pending, remove them
    pending = event.setdefault("pending", [])
    if user_id in pending:
        pending.remove(user_id)
    return True

def subscribe_user_to_event(event_id: str, user_id: str) -> bool:
    event = EVENTS.get(event_id)
    if not event:
        return False
    assigned = event.setdefault("assigned", [])
    if user_id in assigned:
        return True # Already assigned
    
    pending = event.setdefault("pending", [])
    if user_id in pending:
        return True # Already pending
        
    pending.append(user_id)
    return True

def confirm_user_assignment(event_id: str, user_id: str) -> bool:
    return assign_user_to_event(event_id, user_id)

def create_availability(user_id: str, start: str, end: str, note: str = "") -> Dict:
    avail_id = str(uuid4())
    rec = {"id": avail_id, "user_id": user_id, "start": start, "end": end, "note": note}
    AVAILABILITIES[avail_id] = rec
    return rec

def list_availabilities():
    return list(AVAILABILITIES.values())

def get_availability_for_user(user_id: str):
    return [a for a in AVAILABILITIES.values() if a.get("user_id") == user_id]
