"""
Shift Validation Module
Validates that employee assignments meet scheduling constraints:
- No overlapping shifts
- Minimum break time between shifts (configurable, default 1 hour)
- Maximum hours per day (configurable, default 12 hours)
"""

from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional


def parse_datetime(date_string: str) -> Optional[datetime]:
    """Parse ISO format datetime string"""
    try:
        if 'T' in date_string:
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return datetime.fromisoformat(date_string)
    except:
        return None


def validate_assignment(
    employee_id: str,
    event: Dict,
    all_events: List[Dict],
    min_break_hours: float = 1.0,
    max_daily_hours: float = 12.0
) -> Tuple[bool, List[Dict]]:
    """
    Validate if an employee can be assigned to an event without conflicts.
    
    Args:
        employee_id: ID of the employee to assign
        event: The event to assign the employee to
        all_events: All events in the system
        min_break_hours: Minimum hours between shifts (default 8)
        max_daily_hours: Maximum hours per day (default 12)
    
    Returns:
        Tuple of (is_valid, conflicts_list)
        - is_valid: True if assignment is allowed
        - conflicts_list: List of conflict dictionaries with 'severity', 'message'
    """
    
    conflicts = []
    
    # Parse event times
    event_start = parse_datetime(event.get('start', ''))
    event_end = parse_datetime(event.get('end', ''))
    
    if not event_start or not event_end:
        return False, [{"severity": "error", "message": "Invalid event time format"}]
    
    # FIX: If end is before start, assume event goes through midnight
    if event_end < event_start:
        event_end = event_end.replace(day=event_end.day + 1)
    
    event_duration = (event_end - event_start).total_seconds() / 3600  # hours
    
    # Find all assignments for this employee
    employee_assignments = []
    for other_event in all_events:
        if other_event.get('id') == event.get('id'):
            continue  # Skip the event being assigned
        
        # Check if employee is assigned to this event
        assigned = other_event.get('assigned', [])
        
        # Ensure assigned is a list (might be string from DB)
        if isinstance(assigned, str):
            assigned = [s.strip() for s in assigned.split(',') if s.strip()]
        elif not isinstance(assigned, list):
            assigned = list(assigned) if assigned else []
        
        if employee_id in assigned:
            other_start = parse_datetime(other_event.get('start', ''))
            other_end = parse_datetime(other_event.get('end', ''))
            if other_start and other_end:
                # FIX: If end is before start, assume event goes through midnight
                if other_end < other_start:
                    other_end = other_end.replace(day=other_end.day + 1)
                
                employee_assignments.append({
                    'event': other_event,
                    'start': other_start,
                    'end': other_end,
                    'duration': (other_end - other_start).total_seconds() / 3600
                })
    
    # Check 1: Overlapping shifts
    for assignment in employee_assignments:
        other_start = assignment['start']
        other_end = assignment['end']
        
        # Check if there's any overlap
        if not (event_end <= other_start or event_start >= other_end):
            conflicts.append({
                "severity": "error",
                "message": f"Overlaps with {assignment['event'].get('title', 'event')} "
                          f"({other_start.strftime('%Y-%m-%d %H:%M')} - "
                          f"{other_end.strftime('%Y-%m-%d %H:%M')})"
            })
    
    # Check 2: Minimum break time between shifts
    for assignment in employee_assignments:
        other_start = assignment['start']
        other_end = assignment['end']
        
        # Break after this event, before the other event
        if event_end <= other_start:
            break_time = (other_start - event_end).total_seconds() / 3600
            if break_time < min_break_hours:
                conflicts.append({
                    "severity": "warning",
                    "message": f"Only {break_time:.1f}h break before next shift "
                              f"(minimum {min_break_hours}h required)"
                })
        
        # Break after the other event, before this event
        if other_end <= event_start:
            break_time = (event_start - other_end).total_seconds() / 3600
            if break_time < min_break_hours:
                conflicts.append({
                    "severity": "warning",
                    "message": f"Only {break_time:.1f}h break after previous shift "
                              f"(minimum {min_break_hours}h required)"
                })
    
    # Check 3: Maximum hours per day
    event_day = event_start.date()
    daily_hours = event_duration
    
    for assignment in employee_assignments:
        other_day = assignment['start'].date()
        if other_day == event_day:
            daily_hours += assignment['duration']
    
    if daily_hours > max_daily_hours:
        conflicts.append({
            "severity": "warning",
            "message": f"Total {daily_hours:.1f}h on {event_day.strftime('%Y-%m-%d')} "
                      f"(maximum {max_daily_hours}h recommended)"
        })
    
    # Assignment is valid if no errors (warnings are allowed)
    has_errors = any(c['severity'] == 'error' for c in conflicts)
    
    return not has_errors, conflicts
