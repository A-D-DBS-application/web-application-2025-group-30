import os
from typing import Dict, List, Optional
from uuid import uuid4
from dotenv import load_dotenv

load_dotenv()

try:
    from supabase import create_client, Client
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        # Fallback for development if env vars are missing, but warn
        print("WARNING: Supabase credentials not found. Using in-memory storage.")
        supabase = None
    else:
        supabase: Client = create_client(url, key)
except (ImportError, ModuleNotFoundError):
    # Fallback if supabase dependencies are not compatible (e.g., Python 3.14)
    print("WARNING: Supabase not available. Using in-memory storage.")
    supabase = None

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

def get_event_by_id(event_id: str):
    if not supabase:
        return _MEM_EVENTS.get(event_id)
    
    res = supabase.table("events").select("*").eq("id", event_id).execute()
    if res.data:
        return res.data[0]
    return None

def update_event(event_id: str, data: Dict) -> bool:
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
    if "hours" in data:
        event_data["hours"] = data.get("hours", "")
    if "assigned" in data:
        event_data["assigned"] = data.get("assigned", [])
    if "pending" in data:
        event_data["pending"] = data.get("pending", [])
    
    if not supabase:
        event = _MEM_EVENTS.get(event_id)
        if event:
            event.update(event_data)
            return True
        return False
    
    res = supabase.table("events").update(event_data).eq("id", event_id).execute()
    return res.data is not None and len(res.data) > 0

def delete_event(event_id: str) -> bool:
    if not supabase:
        if event_id in _MEM_EVENTS:
            del _MEM_EVENTS[event_id]
            return True
        return False
    
    res = supabase.table("events").delete().eq("id", event_id).execute()
    return True

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

def is_employee_available(user_id: str, event_start: str, event_end: str) -> bool:
    """
    Check if an employee is available during the event time.
    An employee is available if they have submitted an availability window that covers the event time.
    
    Args:
        user_id: Employee ID
        event_start: Event start time (ISO format like "2025-12-04T14:00")
        event_end: Event end time (ISO format like "2025-12-04T18:00")
    
    Returns:
        True if employee has availability covering this time, False otherwise
    """
    from datetime import datetime
    
    # Parse event times
    try:
        event_start_dt = datetime.fromisoformat(event_start.replace('Z', '+00:00'))
        event_end_dt = datetime.fromisoformat(event_end.replace('Z', '+00:00'))
    except:
        return False
    
    # Get employee's availability windows
    availabilities = get_availability_for_user(user_id)
    
    if not availabilities:
        # No availability submitted = not available
        return False
    
    # Check if any availability window covers the event
    for avail in availabilities:
        try:
            avail_start = datetime.fromisoformat(avail.get('start', '').replace('Z', '+00:00'))
            avail_end = datetime.fromisoformat(avail.get('end', '').replace('Z', '+00:00'))
            
            # Event is covered if it falls within availability window
            if avail_start <= event_start_dt and avail_end >= event_end_dt:
                return True
        except:
            continue
    
    return False

def list_users():
    if not supabase:
        return list(_MEM_USERS.values())
    res = supabase.table("users").select("*").execute()
    return res.data

def search_and_filter_events(events, search_query="", filter_understaffed=False, filter_date_start="", filter_date_end=""):
    """
    Search and filter events by name, location, staffing status, and date range.
    
    Args:
        events: List of event dictionaries
        search_query: Search term for event title or location (case-insensitive)
        filter_understaffed: If True, only show events not fully staffed
        filter_date_start: Filter events on or after this date (format: YYYY-MM-DD)
        filter_date_end: Filter events on or before this date (format: YYYY-MM-DD)
    
    Returns:
        Filtered list of events
    """
    from datetime import datetime
    
    filtered = events
    
    # Search by title or location
    if search_query:
        search_lower = search_query.lower()
        filtered = [
            e for e in filtered 
            if search_lower in (e.get('title') or '').lower() 
            or search_lower in (e.get('location') or '').lower()
        ]
    
    # Filter understaffed events
    if filter_understaffed:
        filtered = [
            e for e in filtered 
            if len(e.get('assigned') or []) < int(e.get('capacity') or 1)
        ]
    
    # Filter by date range
    if filter_date_start:
        try:
            start_dt = datetime.strptime(filter_date_start, '%Y-%m-%d')
            filtered = [
                e for e in filtered 
                if datetime.fromisoformat(e.get('start', '').replace('Z', '+00:00').split('T')[0]) >= start_dt
            ]
        except:
            pass
    
    if filter_date_end:
        try:
            end_dt = datetime.strptime(filter_date_end, '%Y-%m-%d')
            filtered = [
                e for e in filtered 
                if datetime.fromisoformat(e.get('start', '').replace('Z', '+00:00').split('T')[0]) <= end_dt
            ]
        except:
            pass
    
    return filtered

def calculate_statistics(events, employees, availabilities=None):
    """
    Calculate comprehensive statistics for dashboard.
    
    Returns dictionary with:
    - Weekly/monthly overview stats
    - Individual employee statistics with utilization rate based on availability hours
    """
    from datetime import datetime, timedelta
    
    if availabilities is None:
        availabilities = []
    
    stats = {
        "total_events": len(events),
        "fully_filled_events": 0,
        "understaffed_events": 0,
        "pending_approvals": 0,
        "total_shifts_filled": 0,
        "total_capacity": 0,
        "fill_rate_percentage": 0,
        "employee_stats": []
    }
    
    # Calculate event statistics
    for event in events:
        assigned_count = len(event.get('assigned') or [])
        pending_count = len(event.get('pending') or [])
        capacity = int(event.get('capacity') or 1)
        
        stats["total_capacity"] += capacity
        stats["total_shifts_filled"] += assigned_count
        stats["pending_approvals"] += pending_count
        
        if assigned_count >= capacity:
            stats["fully_filled_events"] += 1
        elif assigned_count < capacity:
            stats["understaffed_events"] += 1
    
    # Calculate fill rate
    if stats["total_capacity"] > 0:
        stats["fill_rate_percentage"] = round((stats["total_shifts_filled"] / stats["total_capacity"]) * 100, 1)
    
    # Calculate employee statistics
    for emp in employees:
        emp_id = emp.get('id')
        emp_username = emp.get('username')
        
        # Count shifts assigned to employee
        assigned_shifts = [e for e in events if emp_id in (e.get('assigned') or [])]
        total_hours = 0
        
        # Calculate total hours worked
        for event in assigned_shifts:
            try:
                start = datetime.fromisoformat(event.get('start', '').replace('Z', '+00:00'))
                end = datetime.fromisoformat(event.get('end', '').replace('Z', '+00:00'))
                hours = (end - start).total_seconds() / 3600
                # Only add positive hours (ignore negative or invalid time ranges)
                if hours > 0:
                    total_hours += hours
            except:
                pass
        
        # Calculate total available hours for this employee
        total_available_hours = 0
        emp_availabilities = [a for a in availabilities if a.get('user_id') == emp_id]
        
        for avail in emp_availabilities:
            try:
                start = datetime.fromisoformat(avail.get('start', '').replace('Z', '+00:00'))
                end = datetime.fromisoformat(avail.get('end', '').replace('Z', '+00:00'))
                hours = (end - start).total_seconds() / 3600
                # Only add positive hours (ignore negative or invalid time ranges)
                if hours > 0:
                    total_available_hours += hours
            except:
                pass
        
        # Calculate utilization rate (hours worked / hours available)
        utilization_rate = 0
        if total_available_hours > 0:
            utilization_rate = round((total_hours / total_available_hours) * 100, 1)
        
        if len(assigned_shifts) > 0 or total_hours > 0:
            stats["employee_stats"].append({
                "username": emp_username,
                "shifts_assigned": len(assigned_shifts),
                "total_hours": round(total_hours, 1),
                "utilization_rate": utilization_rate
            })
    
    # Sort employees by hours worked (descending)
    stats["employee_stats"].sort(key=lambda x: x['total_hours'], reverse=True)
    
    return stats
