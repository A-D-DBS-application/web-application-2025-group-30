import os
from typing import Dict, List, Optional
from uuid import uuid4
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    # Fallback for development if env vars are missing, but warn
    print("WARNING: Supabase credentials not found. Using in-memory storage.")
    supabase = None
else:
    supabase: Client = create_client(url, key)

# In-memory fallback (only used if supabase init fails)
_MEM_USERS = {}
_MEM_EVENTS = {}
_MEM_AVAIL = {}

def create_user(username: str, hashed_password: str, role: str = "employee") -> Dict:
    if not supabase:
        user_id = str(uuid4())
        user = {"id": user_id, "username": username, "password": hashed_password, "role": role}
        _MEM_USERS[user_id] = user
        return user
    
    # Supabase Insert
    # Note: We are using a public 'users' table for simplicity to match existing logic.
    # Ideally, use supabase.auth.sign_up() but that requires changing auth flow.
    data = {
        "username": username,
        "password": hashed_password, # Storing plain/hashed as per current logic
        "role": role
    }
    res = supabase.table("users").insert(data).execute()
    if res.data:
        return res.data[0]
    return {}

def find_user_by_username(username: str):
    if not supabase:
        for u in _MEM_USERS.values():
            if u["username"] == username:
                return u
        return None
        
    res = supabase.table("users").select("*").eq("username", username).execute()
    if res.data:
        return res.data[0]
    return None

def get_user_public(user: Dict) -> Dict:
    return {"id": user["id"], "username": user["username"], "role": user.get("role", "employee")}

def create_event(data: Dict) -> Dict:
    # normalize fields
    event_data = {
        "title": data.get("title") or data.get("name"),
        "description": data.get("description", ""),
        "start": data.get("start"),
        "end": data.get("end"),
        "capacity": int(data.get("capacity", data.get("amount", 1))),
        "type": data.get("type", "general"),
        "location": data.get("location", ""),
        "hours": data.get("hours", ""),
        "assigned": data.get("assigned", []), # JSONB list of user_ids
        "pending": data.get("pending", []),   # JSONB list of user_ids
    }

    if not supabase:
        event_id = str(uuid4())
        event_data["id"] = event_id
        _MEM_EVENTS[event_id] = event_data
        return event_data

    res = supabase.table("events").insert(event_data).execute()
    if res.data:
        return res.data[0]
    return {}

def list_events():
    if not supabase:
        return list(_MEM_EVENTS.values())
    
    res = supabase.table("events").select("*").execute()
    return res.data

def assign_user_to_event(event_id: str, user_id: str) -> bool:
    if not supabase:
        event = _MEM_EVENTS.get(event_id)
        if not event: return False
        assigned = event.setdefault("assigned", [])
        if user_id in assigned: return True
        if len(assigned) >= int(event.get("capacity", 1)): return False
        assigned.append(user_id)
        pending = event.setdefault("pending", [])
        if user_id in pending: pending.remove(user_id)
        return True

    # Fetch current event to check capacity and current lists
    res = supabase.table("events").select("*").eq("id", event_id).execute()
    if not res.data:
        return False
    
    event = res.data[0]
    assigned = event.get("assigned") or []
    pending = event.get("pending") or []
    capacity = event.get("capacity", 1)

    if user_id in assigned:
        return True
    
    if len(assigned) >= capacity:
        return False
    
    assigned.append(user_id)
    if user_id in pending:
        pending.remove(user_id)
    
    # Update
    supabase.table("events").update({"assigned": assigned, "pending": pending}).eq("id", event_id).execute()
    return True

def subscribe_user_to_event(event_id: str, user_id: str) -> bool:
    if not supabase:
        event = _MEM_EVENTS.get(event_id)
        if not event: return False
        assigned = event.setdefault("assigned", [])
        if user_id in assigned: return True
        pending = event.setdefault("pending", [])
        if user_id in pending: return True
        pending.append(user_id)
        return True

    res = supabase.table("events").select("*").eq("id", event_id).execute()
    if not res.data:
        return False
    
    event = res.data[0]
    assigned = event.get("assigned") or []
    pending = event.get("pending") or []

    if user_id in assigned:
        return True
    
    if user_id not in pending:
        pending.append(user_id)
        supabase.table("events").update({"pending": pending}).eq("id", event_id).execute()
    
    return True

def confirm_user_assignment(event_id: str, user_id: str) -> bool:
    return assign_user_to_event(event_id, user_id)

def create_availability(user_id: str, start: str, end: str, note: str = "") -> Dict:
    data = {"user_id": user_id, "start": start, "end": end, "note": note}
    
    if not supabase:
        avail_id = str(uuid4())
        data["id"] = avail_id
        _MEM_AVAIL[avail_id] = data
        return data

    res = supabase.table("availabilities").insert(data).execute()
    if res.data:
        return res.data[0]
    return {}

def list_availabilities():
    if not supabase:
        return list(_MEM_AVAIL.values())
    res = supabase.table("availabilities").select("*").execute()
    return res.data

def get_availability_for_user(user_id: str):
    if not supabase:
        return [a for a in _MEM_AVAIL.values() if a.get("user_id") == user_id]
    
    res = supabase.table("availabilities").select("*").eq("user_id", user_id).execute()
    return res.data

def get_user_by_id(user_id: str):
    if not supabase:
        return _MEM_USERS.get(user_id)
    
    res = supabase.table("users").select("*").eq("id", user_id).execute()
    if res.data:
        return res.data[0]
    return None

def list_users():
    if not supabase:
        return list(_MEM_USERS.values())
    res = supabase.table("users").select("*").execute()
    return res.data
