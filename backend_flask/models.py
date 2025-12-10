import os
from typing import Dict, List, Optional
from uuid import uuid4
from supabase import create_client, Client
from dotenv import load_dotenv
import secrets
import string

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
_MEM_COMPANIES = {}
_MEM_EVENTS = {}
_MEM_AVAIL = {}

def create_company(name: str, logo_url: str = None, owner_id: str = None) -> Dict:
    """Create a new company with a registration code"""
    registration_code = generate_registration_code()
    
    if not supabase:
        company_id = str(uuid4())
        company = {
            "id": company_id,
            "name": name,
            "logo_url": logo_url,
            "registration_code": registration_code,
            "owner_id": owner_id,
            "created_at": None
        }
        _MEM_COMPANIES[company_id] = company
        return company
    
    try:
        company_data = {
            "name": name,
            "logo_url": logo_url,
            "registration_code": registration_code,
            "owner_id": owner_id
        }
        res = supabase.table("companies").insert(company_data).execute()
        if res.data:
            return res.data[0]
    except Exception as e:
        print(f"Error creating company: {e}")
        # Fallback to in-memory
        company_id = str(uuid4())
        company = {
            "id": company_id,
            "name": name,
            "logo_url": logo_url,
            "registration_code": registration_code,
            "owner_id": owner_id,
            "created_at": None
        }
        _MEM_COMPANIES[company_id] = company
        return company
    
    return None

def generate_registration_code(length: int = 8) -> str:
    """Generate a random registration code (e.g., ABC123XY)"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

def get_company_by_code(code: str) -> Dict:
    """Get company by registration code"""
    if not code:
        return None
    
    if not supabase:
        # Check in-memory companies (not ideal but for fallback)
        for company in _MEM_COMPANIES.values():
            if company.get("registration_code") == code:
                return company
        return None
    
    try:
        res = supabase.table("companies").select("*").eq("registration_code", code).execute()
        if res.data:
            return res.data[0]
    except:
        pass
    return None

def validate_registration_code(code: str) -> tuple[bool, str]:
    """Validate a registration code. Returns (is_valid, error_message)"""
    if not code or not code.strip():
        return False, "Registration code is required"
    
    company = get_company_by_code(code.strip().upper())
    if not company:
        return False, "Invalid registration code"
    
    return True, ""

def get_company_by_id(company_id: str) -> Dict:
    """Get company by ID"""
    if not company_id:
        return None
    
    if company_id in _MEM_COMPANIES:
        return _MEM_COMPANIES[company_id]
    
    if not supabase:
        return None
    
    try:
        res = supabase.table("companies").select("*").eq("id", company_id).execute()
        if res.data:
            return res.data[0]
    except:
        pass
    return None

def list_companies() -> List[Dict]:
    """List all companies (used to check if system has any companies)"""
    if not supabase:
        return list(_MEM_COMPANIES.values())
    
    try:
        res = supabase.table("companies").select("*").execute()
        return res.data if res.data else []
    except:
        return list(_MEM_COMPANIES.values())

def create_user(username: str, hashed_password: str, role: str = "employee", company_id: str = None) -> Dict:
    if not supabase:
        user_id = str(uuid4())
        user = {"id": user_id, "username": username, "password": hashed_password, "role": role, "company_id": company_id}
        _MEM_USERS[user_id] = user
        return user
    
    # Supabase Insert
    data = {
        "username": username,
        "password": hashed_password,
        "role": role
    }
    if company_id:
        data["company_id"] = company_id
    
    try:
        res = supabase.table("users").insert(data).execute()
        if res.data:
            return res.data[0]
    except Exception as e:
        print(f"Error inserting user with company_id: {e}")
        # Fallback: try without company_id
        try:
            data_no_company = {k: v for k, v in data.items() if k != "company_id"}
            res = supabase.table("users").insert(data_no_company).execute()
            if res.data:
                user = res.data[0]
                if company_id:
                    user["company_id"] = company_id
                return user
        except Exception as e2:
            print(f"Error inserting user even without company_id: {e2}")
            # Final fallback to in-memory
            user_id = str(uuid4())
            user = {"id": user_id, "username": username, "password": hashed_password, "role": role, "company_id": company_id}
            _MEM_USERS[user_id] = user
            return user
    
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

def create_event(data: Dict, company_id: str = None) -> Dict:
    # normalize fields
    event_data = {
        "title": data.get("title") or data.get("name"),
        "description": data.get("description", ""),
        "start": data.get("start"),
        "end": data.get("end"),
        "capacity": int(data.get("capacity", data.get("amount", 1))),
        "type": data.get("type", "general"),
        "location": data.get("location", "")
    }
    
    # Add company_id if provided
    if company_id:
        event_data["company_id"] = company_id

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
        print(f"Error inserting event with company_id: {e}")
        # Fallback: try without company_id if it fails (schema not updated)
        try:
            event_data_no_company = {k: v for k, v in event_data.items() if k != "company_id"}
            res = supabase.table("events").insert(event_data_no_company).execute()
            if res.data:
                event = res.data[0]
                # Add company_id to local copy if provided
                if company_id:
                    event["company_id"] = company_id
                return event
        except Exception as e2:
            print(f"Error inserting event even without company_id: {e2}")
            # Final fallback to in-memory
            event_id = str(uuid4())
            event_data["id"] = event_id
            _MEM_EVENTS[event_id] = event_data
            return event_data
    
    return {}

def list_events(company_id: str = None):
    if not supabase:
        events = list(_MEM_EVENTS.values())
        if company_id:
            events = [e for e in events if e.get("company_id") == company_id]
        return _enrich_events_with_assignments(events)
    
    try:
        if company_id:
            res = supabase.table("events").select("*").eq("company_id", company_id).execute()
        else:
            res = supabase.table("events").select("*").execute()
        events = res.data if res.data else []
    except Exception as e:
        print(f"Error querying events with company_id filter: {e}")
        # Fallback: get all events without company_id filter (schema might not be updated yet)
        try:
            res = supabase.table("events").select("*").execute()
            events = res.data if res.data else []
            # If company_id is requested, filter in memory
            if company_id:
                events = [e for e in events if e.get("company_id") == company_id]
        except:
            events = list(_MEM_EVENTS.values())
    
    return _enrich_events_with_assignments(events)

def _enrich_events_with_assignments(events: List[Dict]) -> List[Dict]:
    """Add assigned and pending user lists to events from event_assignments table"""
    if not supabase:
        return events
    
    for event in events:
        event_id = event.get("id")
        if not event_id:
            continue
        
        try:
            # Get confirmed assignments
            confirmed = supabase.table("event_assignments").select("user_id").eq("event_id", event_id).eq("status", "confirmed").execute()
            event["assigned"] = [r["user_id"] for r in confirmed.data] if confirmed.data else []
            
            # Get pending assignments
            pending_res = supabase.table("event_assignments").select("user_id").eq("event_id", event_id).eq("status", "pending").execute()
            event["pending"] = [r["user_id"] for r in pending_res.data] if pending_res.data else []
        except Exception as e:
            print(f"Error enriching event {event_id}: {e}")
            event["assigned"] = []
            event["pending"] = []
    
    return events

def get_event_by_id(event_id: str):
    if not supabase:
        event = _MEM_EVENTS.get(event_id)
        return event
    
    res = supabase.table("events").select("*").eq("id", event_id).execute()
    if res.data:
        event = res.data[0]
        # Enrich with assignments
        enriched = _enrich_events_with_assignments([event])
        return enriched[0] if enriched else event
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

    try:
        # CRITICAL: Validate that user exists before assigning
        user = get_user_by_id(user_id)
        if not user:
            print(f"Cannot assign: user {user_id} does not exist")
            return False
        
        # Get event to check capacity
        event = get_event_by_id(event_id)
        if not event:
            return False
        
        # Check if already assigned
        res = supabase.table("event_assignments").select("*").eq("event_id", event_id).eq("user_id", user_id).execute()
        if res.data:
            # Update status to confirmed if it exists
            supabase.table("event_assignments").update({"status": "confirmed"}).eq("event_id", event_id).eq("user_id", user_id).execute()
            return True
        
        # Check capacity
        capacity = event.get("capacity", 1)
        count_res = supabase.table("event_assignments").select("*").eq("event_id", event_id).eq("status", "confirmed").execute()
        if len(count_res.data) >= capacity:
            return False
        
        # Insert as confirmed assignment
        supabase.table("event_assignments").insert({
            "event_id": event_id,
            "user_id": user_id,
            "status": "confirmed"
        }).execute()
        return True
    except Exception as e:
        print(f"Error assigning user to event: {e}")
        return False

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

    try:
        # Check if user is already assigned or pending
        res = supabase.table("event_assignments").select("*").eq("event_id", event_id).eq("user_id", user_id).execute()
        if res.data:
            return True
        
        # Insert as pending assignment
        supabase.table("event_assignments").insert({
            "event_id": event_id,
            "user_id": user_id,
            "status": "pending"
        }).execute()
        return True
    except Exception as e:
        print(f"Error subscribing user to event: {e}")
        return False

def unassign_user_from_event(event_id: str, user_id: str) -> bool:
    """Remove a user's assignment from an event"""
    if not supabase:
        return True
    
    try:
        supabase.table("event_assignments").delete().eq("event_id", event_id).eq("user_id", user_id).execute()
        return True
    except Exception as e:
        print(f"Error unassigning user from event: {e}")
        return False

def confirm_user_assignment(event_id: str, user_id: str) -> bool:
    return assign_user_to_event(event_id, user_id)

def create_availability(user_id: str, start: str, end: str, note: str = "", company_id: str = None) -> Dict:
    data = {"user_id": user_id, "start": start, "end": end, "note": note}
    
    if company_id:
        data["company_id"] = company_id
    
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
        print(f"Error inserting availability with company_id: {e}")
        # Fallback: try without company_id if it fails
        try:
            data_no_company = {k: v for k, v in data.items() if k != "company_id"}
            res = supabase.table("availabilities").insert(data_no_company).execute()
            if res.data:
                avail = res.data[0]
                if company_id:
                    avail["company_id"] = company_id
                return avail
        except Exception as e2:
            print(f"Error inserting availability even without company_id: {e2}")
            # Final fallback to in-memory
            avail_id = str(uuid4())
            data["id"] = avail_id
            _MEM_AVAIL[avail_id] = data
            return data
    
    return {}

def list_availabilities(company_id: str = None):
    if not supabase:
        avails = list(_MEM_AVAIL.values())
        if company_id:
            avails = [a for a in avails if a.get("company_id") == company_id]
        return avails
    
    try:
        if company_id:
            res = supabase.table("availabilities").select("*").eq("company_id", company_id).execute()
        else:
            res = supabase.table("availabilities").select("*").execute()
        return res.data
    except Exception as e:
        print(f"Error querying availabilities with company_id filter: {e}")
        # Fallback: get all availabilities and filter in memory
        try:
            res = supabase.table("availabilities").select("*").execute()
            avails = res.data if res.data else []
            if company_id:
                avails = [a for a in avails if a.get("company_id") == company_id]
            return avails
        except:
            return list(_MEM_AVAIL.values())

def get_availability_for_user(user_id: str, company_id: str = None):
    if not supabase:
        avails = [a for a in _MEM_AVAIL.values() if a.get("user_id") == user_id]
        if company_id:
            avails = [a for a in avails if a.get("company_id") == company_id]
        return avails
    
    try:
        if company_id:
            res = supabase.table("availabilities").select("*").eq("user_id", user_id).eq("company_id", company_id).execute()
        else:
            res = supabase.table("availabilities").select("*").eq("user_id", user_id).execute()
        return res.data
    except Exception as e:
        print(f"Error querying availabilities for user: {e}")
        # Fallback: get all and filter in memory
        try:
            res = supabase.table("availabilities").select("*").eq("user_id", user_id).execute()
            avails = res.data if res.data else []
            if company_id:
                avails = [a for a in avails if a.get("company_id") == company_id]
            return avails
        except:
            avails = [a for a in _MEM_AVAIL.values() if a.get("user_id") == user_id]
            if company_id:
                avails = [a for a in avails if a.get("company_id") == company_id]
            return avails

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

def get_user_assigned_events(user_id: str) -> List[Dict]:
    """Get all events assigned to a specific user"""
    try:
        if not supabase:
            return []
        
        # Get event_ids assigned to this user from event_assignments table
        assignments = supabase.table("event_assignments").select("event_id").eq("user_id", user_id).execute()
        if not assignments.data:
            return []
        
        event_ids = [a["event_id"] for a in assignments.data]
        
        # Get all events and filter by event_ids
        all_events = list_events()
        user_events = [e for e in all_events if e.get("id") in event_ids]
        return user_events
    except Exception as e:
        print(f"Error getting user assigned events: {e}")
        return []

def list_users(company_id: str = None):
    if not supabase:
        users = list(_MEM_USERS.values())
        if company_id:
            users = [u for u in users if u.get("company_id") == company_id]
        return users
    
    try:
        if company_id:
            res = supabase.table("users").select("*").eq("company_id", company_id).execute()
        else:
            res = supabase.table("users").select("*").execute()
        return res.data
    except Exception as e:
        print(f"Error querying users with company_id filter: {e}")
        # Fallback: get all users and filter in memory
        try:
            res = supabase.table("users").select("*").execute()
            users = res.data if res.data else []
            if company_id:
                users = [u for u in users if u.get("company_id") == company_id]
            return users
        except:
            return list(_MEM_USERS.values())

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
