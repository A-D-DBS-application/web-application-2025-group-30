"""
Conflict Detection Algorithm for Personnel Scheduler

This module identifies scheduling conflicts automatically by:
1. Checking for overlapping shifts for the same employee
2. Detecting employees assigned to impossible time combinations
3. Alerting managers before conflicts are created
4. Validating shift assignments against employee availability

The algorithm can be integrated with the Flask backend to prevent
scheduling errors before they occur.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set, Tuple


class SchedulingConflict:
    """Represents a detected scheduling conflict"""
    
    def __init__(self, conflict_type: str, message: str, employee_id: str, 
                 event_ids: List[str], severity: str = "warning"):
        self.conflict_type = conflict_type
        self.message = message
        self.employee_id = employee_id
        self.event_ids = event_ids
        self.severity = severity  # "warning" or "error"
    
    def to_dict(self):
        """Convert conflict to dictionary for API responses"""
        return {
            "type": self.conflict_type,
            "message": self.message,
            "employee_id": self.employee_id,
            "event_ids": self.event_ids,
            "severity": self.severity
        }
    
    def __repr__(self):
        return f"Conflict({self.conflict_type}, employee={self.employee_id}, events={self.event_ids})"


class ConflictDetector:
    """
    Main conflict detection engine that validates shift assignments
    and identifies scheduling problems before they occur
    """
    
    def __init__(self, min_break_hours: float = 8.0, max_daily_hours: float = 12.0):
        """
        Initialize conflict detector with configurable thresholds
        
        Args:
            min_break_hours: Minimum hours required between shifts (default 8)
            max_daily_hours: Maximum hours an employee can work per day (default 12)
        """
        self.min_break_hours = min_break_hours
        self.max_daily_hours = max_daily_hours
    
    def detect_all_conflicts(self, events: List[dict], employees: List[dict] = None) -> List[SchedulingConflict]:
        """
        Detect all scheduling conflicts across all events and employees
        
        Args:
            events: List of event dictionaries with keys: id, title, start, end, assigned
            employees: Optional list of employee dictionaries (can be used for availability checks)
        
        Returns:
            List of SchedulingConflict objects describing all detected conflicts
        """
        conflicts = []
        
        # Build employee-to-events mapping
        employee_events = self._build_employee_schedule(events)
        
        # Check each employee's schedule for conflicts
        for employee_id, assigned_events in employee_events.items():
            # Sort events by start time
            sorted_events = sorted(assigned_events, key=lambda e: e['start'])
            
            # Check for overlapping shifts
            conflicts.extend(self._check_overlapping_shifts(employee_id, sorted_events))
            
            # Check for insufficient break time
            conflicts.extend(self._check_insufficient_breaks(employee_id, sorted_events))
            
            # Check for excessive daily hours
            conflicts.extend(self._check_daily_hours(employee_id, sorted_events))
        
        return conflicts
    
    def check_new_assignment(self, employee_id: str, new_event: dict, 
                            existing_events: List[dict]) -> List[SchedulingConflict]:
        """
        Check if assigning an employee to a new event would create conflicts
        Use this before confirming a shift assignment
        
        Args:
            employee_id: ID of employee to assign
            new_event: Event dictionary with keys: id, title, start, end
            existing_events: List of events where employee is already assigned
        
        Returns:
            List of conflicts that would be created (empty list if no conflicts)
        """
        conflicts = []
        
        # Filter existing events for this specific employee
        employee_existing = [e for e in existing_events 
                           if employee_id in e.get('assigned', [])]
        
        # Create temporary combined list with new event
        all_events = employee_existing + [new_event]
        sorted_events = sorted(all_events, key=lambda e: e['start'])
        
        # Check all conflict types
        conflicts.extend(self._check_overlapping_shifts(employee_id, sorted_events))
        conflicts.extend(self._check_insufficient_breaks(employee_id, sorted_events))
        conflicts.extend(self._check_daily_hours(employee_id, sorted_events))
        
        # Filter to only conflicts involving the new event
        return [c for c in conflicts if new_event['id'] in c.event_ids]
    
    def _build_employee_schedule(self, events: List[dict]) -> Dict[str, List[dict]]:
        """Build mapping of employee_id -> list of assigned events"""
        schedule = {}
        
        for event in events:
            assigned = event.get('assigned', [])
            for employee_id in assigned:
                if employee_id not in schedule:
                    schedule[employee_id] = []
                schedule[employee_id].append(event)
        
        return schedule
    
    def _check_overlapping_shifts(self, employee_id: str, 
                                  events: List[dict]) -> List[SchedulingConflict]:
        """Detect if employee has overlapping shift times"""
        conflicts = []
        
        for i in range(len(events)):
            for j in range(i + 1, len(events)):
                event_a = events[i]
                event_b = events[j]
                
                # Parse datetime strings
                start_a = self._parse_datetime(event_a['start'])
                end_a = self._parse_datetime(event_a['end'])
                start_b = self._parse_datetime(event_b['start'])
                end_b = self._parse_datetime(event_b['end'])
                
                # Check for overlap: A starts before B ends AND A ends after B starts
                if start_a < end_b and end_a > start_b:
                    conflicts.append(SchedulingConflict(
                        conflict_type="overlapping_shifts",
                        message=f"Employee has overlapping shifts: '{event_a['title']}' and '{event_b['title']}'",
                        employee_id=employee_id,
                        event_ids=[event_a['id'], event_b['id']],
                        severity="error"
                    ))
        
        return conflicts
    
    def _check_insufficient_breaks(self, employee_id: str, 
                                   events: List[dict]) -> List[SchedulingConflict]:
        """Detect if employee has insufficient break time between consecutive shifts"""
        conflicts = []
        
        for i in range(len(events) - 1):
            current_event = events[i]
            next_event = events[i + 1]
            
            current_end = self._parse_datetime(current_event['end'])
            next_start = self._parse_datetime(next_event['start'])
            
            # Calculate break time in hours
            break_time = (next_start - current_end).total_seconds() / 3600
            
            if 0 < break_time < self.min_break_hours:
                conflicts.append(SchedulingConflict(
                    conflict_type="insufficient_break",
                    message=f"Only {break_time:.1f} hours between '{current_event['title']}' and '{next_event['title']}' (minimum: {self.min_break_hours}h)",
                    employee_id=employee_id,
                    event_ids=[current_event['id'], next_event['id']],
                    severity="warning"
                ))
        
        return conflicts
    
    def _check_daily_hours(self, employee_id: str, 
                          events: List[dict]) -> List[SchedulingConflict]:
        """Detect if employee exceeds maximum daily working hours"""
        conflicts = []
        
        # Group events by date
        daily_events = {}
        for event in events:
            start = self._parse_datetime(event['start'])
            date_key = start.date()
            
            if date_key not in daily_events:
                daily_events[date_key] = []
            daily_events[date_key].append(event)
        
        # Check each day's total hours
        for date, day_events in daily_events.items():
            total_hours = 0
            event_ids = []
            
            for event in day_events:
                start = self._parse_datetime(event['start'])
                end = self._parse_datetime(event['end'])
                duration = (end - start).total_seconds() / 3600
                total_hours += duration
                event_ids.append(event['id'])
            
            if total_hours > self.max_daily_hours:
                event_titles = [e['title'] for e in day_events]
                conflicts.append(SchedulingConflict(
                    conflict_type="excessive_daily_hours",
                    message=f"Employee works {total_hours:.1f} hours on {date} (maximum: {self.max_daily_hours}h): {', '.join(event_titles)}",
                    employee_id=employee_id,
                    event_ids=event_ids,
                    severity="warning"
                ))
        
        return conflicts
    
    def _parse_datetime(self, dt_string: str) -> datetime:
        """Parse datetime string in ISO format or common formats"""
        # Try ISO format first
        try:
            return datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        except:
            pass
        
        # Try common formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%dT%H:%M"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(dt_string, fmt)
            except:
                continue
        
        raise ValueError(f"Could not parse datetime string: {dt_string}")


# Utility functions for easy integration

def validate_assignment(employee_id: str, event: dict, all_events: List[dict], 
                       min_break_hours: float = 8.0, max_daily_hours: float = 12.0) -> Tuple[bool, List[dict]]:
    """
    Validate if assigning an employee to an event would create conflicts
    
    Args:
        employee_id: ID of employee to assign
        event: Event dictionary to assign employee to
        all_events: All events in the system
        min_break_hours: Minimum break time between shifts
        max_daily_hours: Maximum working hours per day
    
    Returns:
        Tuple of (is_valid, list of conflict dictionaries)
    """
    detector = ConflictDetector(min_break_hours, max_daily_hours)
    conflicts = detector.check_new_assignment(employee_id, event, all_events)
    
    return len(conflicts) == 0, [c.to_dict() for c in conflicts]


def get_all_conflicts(events: List[dict], min_break_hours: float = 8.0, 
                     max_daily_hours: float = 12.0) -> List[dict]:
    """
    Get all scheduling conflicts across all events
    
    Args:
        events: List of all event dictionaries
        min_break_hours: Minimum break time between shifts
        max_daily_hours: Maximum working hours per day
    
    Returns:
        List of conflict dictionaries
    """
    detector = ConflictDetector(min_break_hours, max_daily_hours)
    conflicts = detector.detect_all_conflicts(events)
    
    return [c.to_dict() for c in conflicts]


# Example usage and testing

if __name__ == "__main__":
    # Test data
    test_events = [
        {
            "id": "evt1",
            "title": "Morning Shift",
            "start": "2025-12-03 08:00:00",
            "end": "2025-12-03 16:00:00",
            "assigned": ["emp1", "emp2"]
        },
        {
            "id": "evt2",
            "title": "Evening Shift",
            "start": "2025-12-03 18:00:00",
            "end": "2025-12-03 23:00:00",
            "assigned": ["emp1"]
        },
        {
            "id": "evt3",
            "title": "Overlapping Event",
            "start": "2025-12-03 14:00:00",
            "end": "2025-12-03 20:00:00",
            "assigned": ["emp2"]
        }
    ]
    
    print("=== Conflict Detection Test ===\n")
    
    # Detect all conflicts
    all_conflicts = get_all_conflicts(test_events)
    
    print(f"Found {len(all_conflicts)} conflicts:\n")
    for conflict in all_conflicts:
        print(f"[{conflict['severity'].upper()}] {conflict['type']}")
        print(f"  Employee: {conflict['employee_id']}")
        print(f"  {conflict['message']}")
        print(f"  Affected events: {conflict['event_ids']}\n")
    
    # Test new assignment validation
    new_event = {
        "id": "evt4",
        "title": "Late Night Shift",
        "start": "2025-12-03 23:30:00",
        "end": "2025-12-04 02:00:00"
    }
    
    is_valid, conflicts = validate_assignment("emp1", new_event, test_events)
    
    print(f"\n=== Testing New Assignment for emp1 ===")
    print(f"Valid: {is_valid}")
    if not is_valid:
        print(f"Conflicts: {conflicts}")
