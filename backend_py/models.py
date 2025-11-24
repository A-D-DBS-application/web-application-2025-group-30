from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from uuid import uuid4

# Pydantic models
class UserIn(BaseModel):
    username: str
    password: str
    role: Optional[str] = "employee"

class UserOut(BaseModel):
    id: str
    username: str
    role: str

class EventIn(BaseModel):
    title: str
    start: str
    end: str
    assigned_to: Optional[str] = None

class EventOut(EventIn):
    id: str

# Very small in-memory "DB" for quick development/demo
USERS: Dict[str, Dict] = {}
EVENTS: Dict[str, Dict] = {}

# helper utilities
def create_user(username: str, hashed_password: str, role: str = "employee") -> Dict:
    _id = str(uuid4())
    user = {"id": _id, "username": username, "password": hashed_password, "role": role}
    USERS[_id] = user
    return user

def find_user_by_username(username: str):
    for u in USERS.values():
        if u["username"] == username:
            return u
    return None

def create_event(data: Dict) -> Dict:
    _id = str(uuid4())
    event = {"id": _id, **data}
    EVENTS[_id] = event
    return event

