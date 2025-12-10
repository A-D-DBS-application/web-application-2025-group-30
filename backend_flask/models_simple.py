import os
from typing import Dict, List, Optional
from uuid import uuid4
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("WARNING: Supabase credentials not found. Using in-memory storage.")
    supabase = None
else:
    supabase: Client = create_client(url, key)

# In-memory fallback
_MEM_USERS = {}
_MEM_EVENTS = {}
_MEM_AVAIL = {}

# ============ USERS ============

def create_user(username: str, hashed_password: str, role: str = "employee") -> Dict:
    """Create a new user"""
    if not supabase:
        user_id = str(uuid4())
        user = {"id": user_id, "username": username, "password": hashed_password, "role": role}
        _MEM_USERS[user_id] = user
        return user
    
    try:
        data = {"username": username, "password": hashed_password, "role": role}
        res = supabase.table("users").insert(data).execute()
        if res.data:
            return res.data[0]
    except Exception as e:
        print(f"Error creating user: {e}")
        user_id = str(uuid4())
        user = {"id": user_id, "username": username, "password": hashed_password, "role": role}
        _MEM_USERS[user_id] = user
        return user
    
    return {}

def find_user_by_username(username: str):
    """Find user by username"""
    if not supabase:
        for u in _MEM_USERS.values():
            if u["username"] == username:
                return u
        return None
    
    try:
        res = supabase.table("users").select("*").eq("username", username).execute()
        if res.data:
            return res.data[0]
    except:
        pass
    return None

def get_user_by_id(user_id: str):
    """Get user by ID"""
    if not supabase:
        return _MEM_USERS.get(user_id)
    
    try:
        res = supabase.table("users").select("*").eq("id", user_id).execute()
        if res.data:
            return res.data[0]
    except:
        pass
    return None

def list_users() -> List[Dict]:
    """List all users"""
    if not supabase:
        return list(_MEM_USERS.values())
    
    try:
        res = supabase.table("users").select("*").execute()
        return res.data if res.data else []
    except:
        return list(_MEM_USERS.values())

# ============ EVENTS ============

def create_event(data: Dict) -> Dict:
    """Create a new event"""
    event_data = {
        "title": data.get("title") or data.get("name"),
        "description": data.get("description", ""),
        "start": data.get("start"),
        "end": data.get("end"),
        "capacity": int(data.get("capacity", data.get("amount", 1))),
        "type": data.get("type", "general"),
        "location": data.get("location", "")
    }

    if not supabase:
        event_id = str(uuid4())
        event_data["id"] = event_id
        _MEM_EVENTS[event_id] = event_data
        return event_data

    try:
        res = supabase.table("events").insert(event_data).execute()
        if res.data:
            return res.data[0]
    except Exception as e:
        print(f"Error creating event: {e}")
        event_id = str(uuid4())
        event_data["id"] = event_id
        _MEM_EVENTS[event_id] = event_data
        return event_data
    
    return {}

def list_events() -> List[Dict]:
    """List all events"""
    if not supabase:
        events = list(_MEM_EVENTS.values())
        return _enrich_events_with_assignments(events)
    
    try:
        res = supabase.table("events").select("*").execute()
        events = res.data if res.data else []
    except Exception as e:
        print(f"Error querying events: {e}")
        events = list(_MEM_EVENTS.values())
    
    return _enrich_events_with_assignments(events)

def get_event_by_id(event_id: str):
    """Get event by ID"""
    if not supabase:
        event = _MEM_EVENTS.get(event_id)
        return event
    
    try:
        res = supabase.table("events").select("*").eq("id", event_id).execute()
        if res.data:
            event = res.data[0]
            enriched = _enrich_events_with_assignments([event])
            return enriched[0] if enriched else event
    except:
        pass
    return None

def update_event(event_id: str, data: Dict) -> bool:
    """Update an event"""
    event_data = {}
    if "title" in data:
        event_data["title"] = data.get("title")
    if "description" in data:
        event_data["description"] = data.get("description", "")
    if "start" in data:
        event_data["start"] = data.get("start")
    if "end" in data:
        event_data["end"] = data.get("end")
    if "capacity" in data:
        event_data["capacity"] = int(data.get("capacity", 1))
    if "location" in data:
        event_data["location"] = data.get("location", "")
    if "type" in data:
        event_data["type"] = data.get("type", "general")
    
    if not supabase:
        event = _MEM_EVENTS.get(event_id)
        if event:
            event.update(event_data)
            return True
        return False
    
    try:
        res = supabase.table("events").update(event_data).eq("id", event_id).execute()
        return res.data is not None and len(res.data) > 0
    except:
        return False

def delete_event(event_id: str) -> bool:
    """Delete an event"""
    if not supabase:
        if event_id in _MEM_EVENTS:
            del _MEM_EVENTS[event_id]
            return True
        return False
    
    try:
        supabase.table("events").delete().eq("id", event_id).execute()
        return True
    except:
        return False

def _enrich_events_with_assignments(events: List[Dict]) -> List[Dict]:
    """Add assigned and pending user lists to events from event_assignments table"""
    if not supabase:
        return events
    
    for event in events:
        event_id = event.get("id")
        if not event_id:
            continue
        
        try:
            confirmed = supabase.table("event_assignments").select("user_id").eq("event_id", event_id).eq("status", "confirmed").execute()
            event["assigned"] = [r["user_id"] for r in confirmed.data] if confirmed.data else []
            
            pending_res = supabase.table("event_assignments").select("user_id").eq("event_id", event_id).eq("status", "pending").execute()
            event["pending"] = [r["user_id"] for r in pending_res.data] if pending_res.data else []
        except:
            event["assigned"] = []
            event["pending"] = []
    
    return events

# ============ EVENT ASSIGNMENTS ============

def assign_user_to_event(event_id: str, user_id: str) -> bool:
    """Assign user to event (confirmed)"""
    if not supabase:
        event = _MEM_EVENTS.get(event_id)
        if not event:
            return False
        assigned = event.setdefault("assigned", [])
        if user_id in assigned:
            return True
        if len(assigned) >= int(event.get("capacity", 1)):
            return False
        assigned.append(user_id)
        pending = event.setdefault("pending", [])
        if user_id in pending:
            pending.remove(user_id)
        return True

    try:
        event = get_event_by_id(event_id)
        if not event:
            return False
        
        res = supabase.table("event_assignments").select("*").eq("event_id", event_id).eq("user_id", user_id).execute()
        if res.data:
            supabase.table("event_assignments").update({"status": "confirmed"}).eq("event_id", event_id).eq("user_id", user_id).execute()
            return True
        
        capacity = event.get("capacity", 1)
        count_res = supabase.table("event_assignments").select("*").eq("event_id", event_id).eq("status", "confirmed").execute()
        if len(count_res.data) >= capacity:
            return False
        
        supabase.table("event_assignments").insert({
            "event_id": event_id,
            "user_id": user_id,
            "status": "confirmed"
        }).execute()
        return True
    except Exception as e:
        print(f"Error assigning user: {e}")
        return False

def subscribe_user_to_event(event_id: str, user_id: str) -> bool:
    """Subscribe user to event (pending)"""
    if not supabase:
        event = _MEM_EVENTS.get(event_id)
        if not event:
            return False
        assigned = event.setdefault("assigned", [])
        if user_id in assigned:
            return True
        pending = event.setdefault("pending", [])
        if user_id in pending:
            return True
        pending.append(user_id)
        return True

    try:
        res = supabase.table("event_assignments").select("*").eq("event_id", event_id).eq("user_id", user_id).execute()
        if res.data:
            return True
        
        supabase.table("event_assignments").insert({
            "event_id": event_id,
            "user_id": user_id,
            "status": "pending"
        }).execute()
        return True
    except Exception as e:
        print(f"Error subscribing user: {e}")
        return False

def unsubscribe_user_from_event(event_id: str, user_id: str) -> bool:
    """Unsubscribe/unassign user from event"""
    if not supabase:
        event = _MEM_EVENTS.get(event_id)
        if not event:
            return False
        assigned = event.get("assigned", [])
        pending = event.get("pending", [])
        if user_id in assigned:
            assigned.remove(user_id)
        if user_id in pending:
            pending.remove(user_id)
        return True

    try:
        supabase.table("event_assignments").delete().eq("event_id", event_id).eq("user_id", user_id).execute()
        return True
    except:
        return False

def confirm_user_for_event(event_id: str, user_id: str) -> bool:
    """Confirm pending user for event"""
    if not supabase:
        event = _MEM_EVENTS.get(event_id)
        if not event:
            return False
        pending = event.get("pending", [])
        if user_id in pending:
            pending.remove(user_id)
        assigned = event.setdefault("assigned", [])
        if user_id not in assigned:
            assigned.append(user_id)
        return True

    try:
        supabase.table("event_assignments").update({"status": "confirmed"}).eq("event_id", event_id).eq("user_id", user_id).execute()
        return True
    except:
        return False

# ============ AVAILABILITIES ============

def create_availability(user_id: str, start: str, end: str, note: str = "") -> Dict:
    """Create availability for user"""
    data = {"user_id": user_id, "start": start, "end": end, "note": note}
    
    if not supabase:
        avail_id = str(uuid4())
        data["id"] = avail_id
        _MEM_AVAIL[avail_id] = data
        return data

    try:
        res = supabase.table("availabilities").insert(data).execute()
        if res.data:
            return res.data[0]
    except Exception as e:
        print(f"Error creating availability: {e}")
        avail_id = str(uuid4())
        data["id"] = avail_id
        _MEM_AVAIL[avail_id] = data
        return data
    
    return {}

def list_availabilities() -> List[Dict]:
    """List all availabilities"""
    if not supabase:
        return list(_MEM_AVAIL.values())
    
    try:
        res = supabase.table("availabilities").select("*").execute()
        return res.data if res.data else []
    except:
        return list(_MEM_AVAIL.values())

def get_availability_for_user(user_id: str) -> List[Dict]:
    """Get availabilities for a user"""
    if not supabase:
        return [a for a in _MEM_AVAIL.values() if a.get("user_id") == user_id]
    
    try:
        res = supabase.table("availabilities").select("*").eq("user_id", user_id).execute()
        return res.data if res.data else []
    except:
        return [a for a in _MEM_AVAIL.values() if a.get("user_id") == user_id]

# ============ SEARCH & FILTER ============

def search_and_filter_events(events, search_query="", filter_understaffed=False, filter_date_start="", filter_date_end=""):
    """Search and filter events"""
    filtered = events
    
    if search_query:
        search_lower = search_query.lower()
        filtered = [e for e in filtered if 
                   search_lower in (e.get("title") or "").lower() or
                   search_lower in (e.get("location") or "").lower()]
    
    if filter_understaffed:
        filtered = [e for e in filtered if 
                   len(e.get("assigned", [])) < int(e.get("capacity", 1))]
    
    if filter_date_start:
        filtered = [e for e in filtered if e.get("start", "") >= filter_date_start]
    
    if filter_date_end:
        filtered = [e for e in filtered if e.get("start", "") <= filter_date_end]
    
    return filtered

def calculate_statistics(events: List[Dict], users: List[Dict], availabilities: List[Dict]) -> Dict:
    """Calculate statistics"""
    total_events = len(events)
    total_users = len(users)
    total_capacity = sum(int(e.get("capacity", 1)) for e in events)
    total_assigned = sum(len(e.get("assigned", [])) for e in events)
    total_pending = sum(len(e.get("pending", [])) for e in events)
    
    upcoming_events = 0
    past_events = 0
    now = datetime.now(timezone.utc)
    
    for event in events:
        try:
            event_start = datetime.fromisoformat(event.get("start", "").replace("Z", "+00:00"))
            if event_start > now:
                upcoming_events += 1
            else:
                past_events += 1
        except:
            upcoming_events += 1
    
    return {
        "total_events": total_events,
        "upcoming_events": upcoming_events,
        "past_events": past_events,
        "total_users": total_users,
        "total_capacity": total_capacity,
        "total_assigned": total_assigned,
        "total_pending": total_pending,
        "coverage": round((total_assigned / total_capacity * 100) if total_capacity > 0 else 0, 1)
    }
