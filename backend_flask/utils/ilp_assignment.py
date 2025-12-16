"""
ILP-Based Employee Assignment Algorithm
Greedy constraint satisfaction approach for shift assignments
Optimized for 40-50 employees with no skill differentiation

Hard Constraints (Must Satisfy):
  1. No overlapping shifts per employee
  2. Minimum 1-hour break between shifts
  3. Maximum 12 hours per employee per day
  4. Availability window constraints
  5. Shift capacity must be met

Soft Constraints (Optimize for Quality):
  1. Fairness: even hour distribution (45% weight)
  2. Availability match: shifts in preferred windows (35% weight)
  3. Reliability: prefer employees with low no-show rates (20% weight)
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple, Optional
from uuid import uuid4


def parse_datetime(date_string: str) -> Optional[datetime]:
    """Parse ISO format datetime string"""
    try:
        if 'T' in date_string:
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return datetime.fromisoformat(date_string)
    except:
        return None


def get_shift_duration_hours(shift: Dict) -> float:
    """Calculate shift duration in hours"""
    try:
        start = parse_datetime(shift.get('start', ''))
        end = parse_datetime(shift.get('end', ''))
        if start and end:
            return (end - start).total_seconds() / 3600
        return 0
    except:
        return 0


def get_shift_date(shift: Dict) -> Optional[str]:
    """Get shift date in YYYY-MM-DD format"""
    try:
        start = parse_datetime(shift.get('start', ''))
        if start:
            return start.strftime('%Y-%m-%d')
        return None
    except:
        return None


def shifts_overlap(shift1: Dict, shift2: Dict) -> bool:
    """Check if two shifts overlap in time"""
    try:
        start1 = parse_datetime(shift1.get('start', ''))
        end1 = parse_datetime(shift1.get('end', ''))
        start2 = parse_datetime(shift2.get('start', ''))
        end2 = parse_datetime(shift2.get('end', ''))
        
        if not all([start1, end1, start2, end2]):
            return False
        
        # Shifts overlap if start of one is before end of other
        return not (end1 <= start2 or end2 <= start1)
    except:
        return False


def has_sufficient_break(shift1: Dict, shift2: Dict, min_break_hours: float = 1.0) -> bool:
    """Check if there's sufficient break between two shifts"""
    try:
        end1 = parse_datetime(shift1.get('end', ''))
        start2 = parse_datetime(shift2.get('start', ''))
        
        if not end1 or not start2:
            return True
        
        if end1 <= start2:
            break_hours = (start2 - end1).total_seconds() / 3600
            return break_hours >= min_break_hours
        
        # Shifts overlap or order is reversed
        return False
    except:
        return True


# ============ HARD CONSTRAINTS ============

def check_no_overlap_constraint(employee_id: str, 
                                shift: Dict, 
                                current_assignments: Dict[str, List[str]],
                                all_events: List[Dict]) -> Tuple[bool, Optional[str]]:
    """
    Hard Constraint 1: Employee cannot work overlapping shifts
    
    Returns: (is_valid, error_message)
    """
    
    # Get all shifts assigned to this employee
    assigned_shift_ids = current_assignments.get(employee_id, [])
    
    # Find full shift objects
    assigned_shifts = [e for e in all_events if e.get('id') in assigned_shift_ids]
    
    # Check for overlaps with new shift
    for assigned_shift in assigned_shifts:
        if shifts_overlap(shift, assigned_shift):
            assigned_title = assigned_shift.get('title', 'Unknown')
            return False, f"Overlaps with {assigned_title}"
    
    return True, None


def check_break_time_constraint(employee_id: str,
                                shift: Dict,
                                current_assignments: Dict[str, List[str]],
                                all_events: List[Dict],
                                min_break_hours: float = 1.0) -> Tuple[bool, Optional[str]]:
    """
    Hard Constraint 2: Minimum break time between shifts (default 1 hour)
    
    Returns: (is_valid, error_message)
    """
    
    assigned_shift_ids = current_assignments.get(employee_id, [])
    assigned_shifts = [e for e in all_events if e.get('id') in assigned_shift_ids]
    
    shift_start = parse_datetime(shift.get('start'))
    shift_end = parse_datetime(shift.get('end'))
    
    for assigned_shift in assigned_shifts:
        assigned_start = parse_datetime(assigned_shift.get('start'))
        assigned_end = parse_datetime(assigned_shift.get('end'))
        
        if not all([shift_start, shift_end, assigned_start, assigned_end]):
            continue
        
        # Case 1: Assigned shift comes first, then new shift
        if assigned_end <= shift_start:
            break_hours = (shift_start - assigned_end).total_seconds() / 3600
            if break_hours < min_break_hours:
                return False, f"Only {break_hours:.1f}h break after previous shift (need {min_break_hours}h)"
        
        # Case 2: New shift comes first, then assigned shift
        elif shift_end <= assigned_start:
            break_hours = (assigned_start - shift_end).total_seconds() / 3600
            if break_hours < min_break_hours:
                return False, f"Only {break_hours:.1f}h break before next shift (need {min_break_hours}h)"
        
        # Case 3: Shifts overlap - handled by no-overlap constraint
    
    return True, None


def check_max_hours_per_day_constraint(employee_id: str,
                                       shift: Dict,
                                       current_assignments: Dict[str, List[str]],
                                       all_events: List[Dict],
                                       max_hours_per_day: float = 12.0) -> Tuple[bool, Optional[str]]:
    """
    Hard Constraint 3: Maximum hours per day (default 12 hours)
    
    Returns: (is_valid, error_message)
    """
    
    shift_date = get_shift_date(shift)
    shift_duration = get_shift_duration_hours(shift)
    
    if not shift_date:
        return True, None
    
    # Sum hours for this employee on this day
    daily_hours = shift_duration
    
    assigned_shift_ids = current_assignments.get(employee_id, [])
    
    for event in all_events:
        if event.get('id') not in assigned_shift_ids:
            continue
        
        event_date = get_shift_date(event)
        if event_date == shift_date:
            daily_hours += get_shift_duration_hours(event)
    
    if daily_hours > max_hours_per_day:
        return False, f"{daily_hours:.1f}h on {shift_date} (max {max_hours_per_day}h)"
    
    return True, None


def check_availability_constraint(employee_id: str,
                                  shift: Dict,
                                  availabilities: List[Dict]) -> Tuple[bool, Optional[str]]:
    """
    Hard Constraint 4: Employee must be within availability window
    
    Returns: (is_valid, error_message)
    """
    
    # Get employee's availability windows
    emp_availabilities = [a for a in availabilities if a.get('user_id') == employee_id]
    
    if not emp_availabilities:
        # No availability submitted = NOT available
        return False, "No availability window submitted"
    
    # Check if shift is within any availability window
    shift_start = parse_datetime(shift.get('start', ''))
    shift_end = parse_datetime(shift.get('end', ''))
    
    if not shift_start or not shift_end:
        return False, "Invalid shift time format"
    
    for avail in emp_availabilities:
        try:
            avail_start = parse_datetime(avail.get('start', ''))
            avail_end = parse_datetime(avail.get('end', ''))
            
            if avail_start and avail_end:
                # Check if ENTIRE shift is within availability window
                if avail_start <= shift_start and shift_end <= avail_end:
                    return True, None
        except:
            pass
    
    return False, "Shift is not fully within any availability window"


def check_capacity_constraint(shift: Dict,
                              current_assignments: Dict[str, List[str]]) -> Tuple[bool, int]:
    """
    Check if shift still needs more people (hard constraint 5)
    
    Returns: (shift_needs_more_people, slots_remaining)
    """
    
    shift_id = shift.get('id')
    capacity = shift.get('capacity', 1)
    
    # Count how many are already assigned
    assigned_count = sum(1 for shift_ids in current_assignments.values() 
                        if shift_id in shift_ids)
    
    slots_remaining = capacity - assigned_count
    needs_more = slots_remaining > 0
    
    return needs_more, max(0, slots_remaining)


def check_all_hard_constraints(employee_id: str,
                               shift: Dict,
                               current_assignments: Dict[str, List[str]],
                               all_events: List[Dict],
                               availabilities: List[Dict]) -> Tuple[bool, List[str]]:
    """
    Check all hard constraints for an assignment
    
    Returns: (is_valid, error_messages)
    """
    
    errors = []
    
    # 1. No overlap
    is_valid, error = check_no_overlap_constraint(employee_id, shift, current_assignments, all_events)
    if not is_valid:
        errors.append(error)
    
    # 2. Break time
    is_valid, error = check_break_time_constraint(employee_id, shift, current_assignments, all_events)
    if not is_valid:
        errors.append(error)
    
    # 3. Max hours per day
    is_valid, error = check_max_hours_per_day_constraint(employee_id, shift, current_assignments, all_events)
    if not is_valid:
        errors.append(error)
    
    # 4. Availability window
    is_valid, error = check_availability_constraint(employee_id, shift, availabilities)
    if not is_valid:
        errors.append(error)
    
    return len(errors) == 0, errors


# ============ SOFT CONSTRAINTS (SCORING) ============

def calculate_fairness_score(employee_id: str,
                            current_assignments: Dict[str, List[str]],
                            all_events: List[Dict]) -> float:
    """
    Soft Constraint 1: Fairness (45% weight)
    
    Employees with fewer hours should be prioritized
    Score: 0.0 (overworked) to 1.0 (underutilized)
    """
    
    # Calculate total hours for all employees
    employee_hours = {}
    
    for emp_id, shift_ids in current_assignments.items():
        total_hours = 0
        for event in all_events:
            if event.get('id') in shift_ids:
                total_hours += get_shift_duration_hours(event)
        employee_hours[emp_id] = total_hours
    
    if not employee_hours:
        return 0.5  # Default if no assignments yet
    
    # Calculate average
    hours_list = list(employee_hours.values())
    avg_hours = sum(hours_list) / len(hours_list)
    
    # Get this employee's hours
    emp_hours = employee_hours.get(employee_id, 0)
    
    # Score: higher if below average, lower if above average
    if avg_hours > 0:
        ratio = emp_hours / avg_hours
        # If ratio is 0.5, score is 1.0 (good)
        # If ratio is 1.5, score is 0.0 (bad)
        fairness_score = max(0.0, 1.0 - ratio)
    else:
        fairness_score = 1.0
    
    return fairness_score


def calculate_availability_match_score(employee_id: str,
                                       shift: Dict,
                                       availabilities: List[Dict]) -> float:
    """
    Soft Constraint 2: Availability Match (35% weight)
    
    Prefer shifts within employee's stated availability windows
    Score: 1.0 (in window), 0.3 (outside window)
    """
    
    emp_availabilities = [a for a in availabilities if a.get('user_id') == employee_id]
    
    if not emp_availabilities:
        return 0.5  # No preferences submitted = neutral
    
    shift_start = parse_datetime(shift.get('start', ''))
    
    if not shift_start:
        return 0.5
    
    # Check if in any availability window
    for avail in emp_availabilities:
        try:
            avail_start = parse_datetime(avail.get('start', ''))
            avail_end = parse_datetime(avail.get('end', ''))
            
            if avail_start and avail_end and avail_start <= shift_start <= avail_end:
                return 1.0  # Perfect match
        except:
            pass
    
    return 0.3  # Outside all availability windows


def calculate_reliability_score(employee_id: str,
                                users: List[Dict]) -> float:
    """
    Soft Constraint 3: Reliability (20% weight)
    
    Score based on historical no-show rate
    For MVP: Use default 0.8 (assume reliable)
    
    Later: Track no-shows in database and calculate actual rate
    no_show_rate = no_shows / total_assignments
    reliability_score = 1.0 - no_show_rate
    """
    
    # Find user in list
    user = next((u for u in users if u.get('id') == employee_id), None)
    
    if not user:
        return 0.8  # Default
    
    # TODO: Implement actual no-show tracking
    # For now, return default reliability score
    
    return 0.8


def calculate_assignment_score(employee_id: str,
                               shift: Dict,
                               current_assignments: Dict[str, List[str]],
                               all_events: List[Dict],
                               availabilities: List[Dict],
                               users: List[Dict],
                               weights: Dict[str, float] = None) -> float:
    """
    Calculate total soft constraint score for an assignment
    
    Combines:
    - Fairness (45%)
    - Availability match (35%)
    - Reliability (20%)
    """
    
    if weights is None:
        weights = {
            'fairness': 0.45,
            'availability': 0.35,
            'reliability': 0.20
        }
    
    # Calculate individual scores
    fairness = calculate_fairness_score(employee_id, current_assignments, all_events)
    availability = calculate_availability_match_score(employee_id, shift, availabilities)
    reliability = calculate_reliability_score(employee_id, users)
    
    # Weighted combination
    total_score = (
        fairness * weights['fairness'] +
        availability * weights['availability'] +
        reliability * weights['reliability']
    )
    
    return total_score


# ============ MAIN ALGORITHM ============

def suggest_assignments(shift: Dict,
                       employees: List[Dict],
                       all_events: List[Dict],
                       availabilities: List[Dict],
                       current_assignments: Dict[str, List[str]],
                       count: int = 5) -> List[Dict]:
    """
    Suggest top N employees for a shift using greedy algorithm
    
    Args:
        shift: The shift to fill
        employees: List of all employees
        all_events: List of all events (for constraint checking)
        availabilities: List of employee availability windows
        current_assignments: Current shift assignments {emp_id: [shift_ids]}
        count: Number of suggestions to return (default 5)
    
    Returns:
        List of suggested employees with scores
        [{
            'employee_id': str,
            'username': str,
            'score': float,
            'breakdown': {
                'fairness': float,
                'availability': float,
                'reliability': float
            },
            'reasons': [str]  # Why this person
        }, ...]
    """
    
    candidates = []
    shift_id = shift.get('id')
    
    # Validate and filter employees list - STRICT validation
    if not employees:
        return []
    
    # Only keep employees with valid IDs
    valid_employees = [e for e in employees if e and e.get('id')]
    if not valid_employees:
        return []
    
    for emp in valid_employees:
        emp_id = emp.get('id')
        
        # Skip any employee without an ID
        if not emp_id:
            continue
        
        # Step 1: Check all hard constraints
        is_valid, errors = check_all_hard_constraints(
            emp_id, shift, current_assignments, all_events, availabilities
        )
        
        if not is_valid:
            continue  # Can't assign this person
        
        # Step 2: Calculate soft constraint scores
        score = calculate_assignment_score(
            emp_id, shift, current_assignments, all_events, availabilities, employees
        )
        
        # Step 3: Build reason strings
        reasons = []
        
        fairness = calculate_fairness_score(emp_id, current_assignments, all_events)
        if fairness > 0.7:
            reasons.append("Has fewer hours than average")
        
        availability = calculate_availability_match_score(emp_id, shift, availabilities)
        if availability > 0.9:
            reasons.append("Shift is in preferred availability window")
        
        reliability = calculate_reliability_score(emp_id, employees)
        if reliability > 0.85:
            reasons.append("Good attendance history")
        
        # Add to candidates
        candidates.append({
            'employee_id': emp_id,
            'username': emp.get('username', 'Unknown'),
            'score': score,
            'breakdown': {
                'fairness': round(fairness, 2),
                'availability': round(availability, 2),
                'reliability': round(reliability, 2)
            },
            'reasons': reasons if reasons else ["Meets all requirements"]
        })
    
    # Step 4: Sort by score and return top N
    candidates.sort(key=lambda x: x['score'], reverse=True)
    return candidates[:count]


def auto_assign_shift(shift: Dict,
                     employees: List[Dict],
                     all_events: List[Dict],
                     availabilities: List[Dict],
                     current_assignments: Dict[str, List[str]],
                     capacity_to_fill: int = None) -> Tuple[List[str], List[str]]:
    """
    Automatically assign employees to fill a shift
    
    Args:
        shift: The shift to fill
        employees: List of all employees
        all_events: List of all events
        availabilities: List of availability windows
        current_assignments: Current assignments
        capacity_to_fill: How many slots to fill (default: shift capacity)
    
    Returns:
        (assigned_employee_ids, errors_if_any)
    """
    
    if capacity_to_fill is None:
        capacity_to_fill = shift.get('capacity', 1)
    
    assigned = []
    errors = []
    
    # Get suggestions for all slots
    suggestions = suggest_assignments(
        shift, employees, all_events, availabilities, current_assignments, 
        count=len(employees)
    )
    
    # Assign top N - only assign valid, existing employees
    employee_ids_set = {e.get('id') for e in employees if e.get('id')}
    
    # Iterate through suggestions until we fill capacity or run out
    for suggestion in suggestions:
        # Stop if we've filled all slots
        if len(assigned) >= capacity_to_fill:
            break
            
        emp_id = suggestion['employee_id']
        
        # Only assign if employee actually exists
        if emp_id not in employee_ids_set:
            continue
        
        # Update assignments
        if emp_id not in current_assignments:
            current_assignments[emp_id] = []
        
        current_assignments[emp_id].append(shift.get('id'))
        assigned.append(emp_id)
    
    # Check if we filled all slots
    if len(assigned) < capacity_to_fill:
        slots_unfilled = capacity_to_fill - len(assigned)
        errors.append(f"Could not fill {slots_unfilled} slots (insufficient eligible employees)")
    
    return assigned, errors


def generate_full_schedule(shifts: List[Dict],
                          employees: List[Dict],
                          availabilities: List[Dict]) -> Dict:
    """
    Generate a full schedule for all shifts
    
    Uses greedy algorithm: process shifts in difficulty order
    
    Args:
        shifts: List of all shifts to fill
        employees: List of all employees
        availabilities: List of availability windows
    
    Returns:
        {
            'assignments': {shift_id: [emp_ids]},
            'coverage': {shift_id: {filled: int, capacity: int}},
            'stats': {
                'total_shifts': int,
                'fully_staffed': int,
                'understaffed': int,
                'fairness_score': float
            }
        }
    """
    
    assignments = {}
    coverage = {}
    
    # Create all_events format for constraint checking
    all_events = shifts
    
    # Sort shifts by difficulty (capacity, then time)
    shifts_sorted = sorted(shifts, key=lambda s: (s.get('capacity', 1), s.get('start', '')), reverse=True)
    
    current_assignments = {}  # {emp_id: [shift_ids]}
    
    # Assign each shift
    for shift in shifts_sorted:
        shift_id = shift.get('id')
        capacity = shift.get('capacity', 1)
        
        assigned, errors = auto_assign_shift(
            shift, employees, all_events, availabilities, current_assignments, capacity
        )
        
        # Map shift_id to list of employee IDs
        assignments[shift_id] = assigned
        coverage[shift_id] = {
            'filled': len(assigned),
            'capacity': capacity,
            'coverage_percent': round(100 * len(assigned) / capacity, 1) if capacity > 0 else 0
        }
    
    # Calculate statistics
    fully_staffed = sum(1 for c in coverage.values() if c['filled'] == c['capacity'])
    understaffed = sum(1 for c in coverage.values() if c['filled'] < c['capacity'])
    
    # Calculate overall fairness
    if current_assignments:
        hours_list = []
        for emp_id, shift_ids in current_assignments.items():
            hours = sum(get_shift_duration_hours(e) for e in all_events if e.get('id') in shift_ids)
            hours_list.append(hours)
        
        if hours_list:
            avg_hours = sum(hours_list) / len(hours_list)
            if avg_hours > 0:
                variance = sum((h - avg_hours) ** 2 for h in hours_list) / len(hours_list)
                std_dev = variance ** 0.5
                fairness_score = max(0.0, 1.0 - (std_dev / avg_hours))
            else:
                fairness_score = 1.0
        else:
            fairness_score = 1.0
    else:
        fairness_score = 1.0
    
    return {
        'assignments': assignments,
        'coverage': coverage,
        'stats': {
            'total_shifts': len(shifts),
            'fully_staffed': fully_staffed,
            'understaffed': understaffed,
            'coverage_percent': round(100 * fully_staffed / len(shifts), 1) if shifts else 0,
            'fairness_score': round(fairness_score, 2)
        }
    }
