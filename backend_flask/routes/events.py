from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template, flash
import os
import jwt
import sys
from datetime import datetime
from models import (create_event, list_events, assign_user_to_event, subscribe_user_to_event, 
                   confirm_user_assignment, get_event_by_id, delete_event, update_event, 
                   is_employee_available, unassign_user_from_event, get_user_assigned_events, 
                   list_users, list_availabilities, create_shift_swap_request, get_swap_requests,
                   approve_shift_swap, reject_shift_swap)
from utils.shift_validator import validate_assignment, ShiftSwapValidator
from utils.ilp_assignment import suggest_assignments, auto_assign_shift

events_bp = Blueprint("events", __name__)
SECRET = os.getenv("SECRET_KEY", "dev-secret")


# ============ HELPER FUNCTIONS ============

def check_auth():
    """Check if user is authenticated. Returns user_id or None."""
    return session.get("user_id")


def validate_and_format_conflicts(conflicts):
    """Format conflict messages for display."""
    conflict_msgs = []
    for conflict in conflicts:
        icon = "❌" if conflict['severity'] == 'error' else "⚠️"
        conflict_msgs.append(f"{icon} {conflict['message']}")
    return " | ".join(conflict_msgs)


def check_assignment_validity(user_id, event, company_id):
    """Check if an employee can be assigned to an event.
    
    Returns: (is_valid, error_message)
    """
    if not is_employee_available(user_id, event.get('start'), event.get('end')):
        return False, "Cannot assign employee: they are not available during this event time"
    
    all_events = list_events(company_id)
    is_valid, conflicts = validate_assignment(user_id, event, all_events)
    
    if not is_valid:
        conflict_msg = validate_and_format_conflicts(conflicts)
        return False, f"Cannot assign employee due to conflicts: {conflict_msg}"
    
    return True, None


def prepare_autofill_data(company_id, shift):
    """Prepare and validate data for autofill operation.
    
    Returns: (employees, all_events, availabilities, valid_employee_ids, current_assignments)
    """
    # Get all data
    employees = list_users(company_id)
    all_events = list_events(company_id)
    availabilities = list_availabilities(company_id)
    
    # Filter out None values and invalid entries
    employees = [e for e in employees if e and e.get('id')]
    all_events = [e for e in all_events if e]
    availabilities = [a for a in availabilities if a]
    
    # Build current assignments
    valid_employee_ids = {e.get('id') for e in employees if e.get('id')}
    current_assignments = {}
    
    for event in all_events:
        for emp_id in event.get('assigned', []):
            if emp_id in valid_employee_ids:
                if emp_id not in current_assignments:
                    current_assignments[emp_id] = []
                current_assignments[emp_id].append(event.get('id'))
    
    return employees, all_events, availabilities, valid_employee_ids, current_assignments


def format_employee_name(employee):
    """Build employee display name from available fields."""
    name = f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip()
    if not name:
        name = employee.get('username', '')
    if not name:
        name = employee.get('email', 'Unknown User')
    return name


def parse_shift_time(event):
    """Parse event datetime to formatted time strings.
    
    Returns: (start_time, end_time) as HH:MM strings
    """
    try:
        start_dt = datetime.fromisoformat(event.get("start", "").replace('Z', '+00:00')) if event.get("start") else None
        end_dt = datetime.fromisoformat(event.get("end", "").replace('Z', '+00:00')) if event.get("end") else None
        start_time = start_dt.strftime('%H:%M') if start_dt else ""
        end_time = end_dt.strftime('%H:%M') if end_dt else ""
    except:
        start_time = event.get("start", "").split("T")[1][:5] if "T" in event.get("start", "") else ""
        end_time = event.get("end", "").split("T")[1][:5] if "T" in event.get("end", "") else ""
    return start_time, end_time


# ============ ROUTES ============


@events_bp.route("/", methods=["GET"])
def get_events():
    # Multi-tenant: only return events for user's company
    company_id = session.get("company_id")
    return jsonify(list_events(company_id))


@events_bp.route("/create", methods=["POST"])
def create_new_event():
    if "user_id" not in session:
        return redirect(url_for("main.index"))
    
    company_id = session.get("company_id")
    if not company_id:
        flash("You must be part of a company to create events", "error")
        return redirect(url_for("main.manager"))
    
    data = request.form
    event_data = dict(data)
    
    # Combine date and time if separate
    if "date" in data and "start_time" in data:
        event_data["start"] = f"{data['date']}T{data['start_time']}"
    if "date" in data and "end_time" in data:
        event_data["end"] = f"{data['date']}T{data['end_time']}"
    
    # Add company_id for multi-tenant isolation
    event_data["company_id"] = company_id
    
    create_event(event_data, company_id)
    return redirect(url_for("main.manager"))


@events_bp.route("/<event_id>/assign", methods=["POST"])
def assign_event(event_id):
    if not check_auth():
        return redirect(url_for("main.index"))
    
    company_id = session.get("company_id")
    data = request.get_json(silent=True) or request.form
    user_id = data.get("user_id")
    
    if not user_id:
        return redirect(url_for("main.manager"))
    
    # Validate assignment
    current_event = get_event_by_id(event_id)
    if current_event:
        is_valid, error_msg = check_assignment_validity(user_id, current_event, company_id)
        if not is_valid:
            flash(error_msg, "error")
            return redirect(url_for("main.manager"))
    
    if assign_user_to_event(event_id, user_id):
        flash("Employee assigned successfully!", "success")
    
    return redirect(url_for("main.manager"))


@events_bp.route("/<event_id>/unassign", methods=["POST"])
def unassign_event(event_id):
    if "user_id" not in session:
        return redirect(url_for("main.index"))
    
    user_id = request.form.get("user_id")
    if not user_id:
        return redirect(url_for("main.manager"))
    
    if unassign_user_from_event(event_id, user_id):
        flash("Employee removed from event successfully!", "success")
    else:
        flash("Error removing employee from event", "error")
    
    return redirect(url_for("main.manager"))


@events_bp.route("/<event_id>/confirm", methods=["POST"])
def confirm_event_subscription(event_id):
    if not check_auth():
        return redirect(url_for("main.index"))
    
    company_id = session.get("company_id")
    user_id = request.form.get("user_id")
    
    if user_id:
        current_event = get_event_by_id(event_id)
        if current_event:
            is_valid, error_msg = check_assignment_validity(user_id, current_event, company_id)
            if not is_valid:
                flash(error_msg, "error")
                return redirect(url_for("main.manager"))
        
        confirm_user_assignment(event_id, user_id)
        flash("Assignment confirmed successfully!", "success")
    
    return redirect(url_for("main.manager"))


@events_bp.route("/<event_id>/subscribe", methods=["POST"])
def subscribe_event(event_id):
    if "user_id" not in session:
        return redirect(url_for("main.index"))
        
    user_id = session["user_id"]
    subscribe_user_to_event(event_id, user_id)
    
    return redirect(url_for("main.dashboard"))


@events_bp.route("/<event_id>/delete", methods=["POST"])
def delete_event_route(event_id):
    if "user_id" not in session:
        return redirect(url_for("main.index"))
    
    delete_event(event_id)
    return redirect(url_for("main.manager"))


@events_bp.route("/<event_id>/edit", methods=["GET"])
def edit_event_form(event_id):
    if "user_id" not in session:
        return redirect(url_for("main.index"))
    
    event = get_event_by_id(event_id)
    if not event:
        return redirect(url_for("main.manager"))
    
    # Parse start and end times
    start_parts = event.get('start', '').split('T')
    date = start_parts[0] if len(start_parts) > 0 else ''
    start_time = start_parts[1][:5] if len(start_parts) > 1 else ''
    
    end_parts = event.get('end', '').split('T')
    end_time = end_parts[1][:5] if len(end_parts) > 1 else ''
    
    return render_template("edit_event.html", event=event, date=date, start_time=start_time, end_time=end_time)


@events_bp.route("/<event_id>/update", methods=["POST"])
def update_event_route(event_id):
    if "user_id" not in session:
        return redirect(url_for("index"))
    
    data = request.form
    event_data = dict(data)
    
    if "date" in data and "start_time" in data:
        event_data["start"] = f"{data['date']}T{data['start_time']}"
    if "date" in data and "end_time" in data:
        event_data["end"] = f"{data['date']}T{data['end_time']}"
    
    update_event(event_id, event_data)
    return redirect(url_for("main.manager"))


@events_bp.route("/shifts", methods=["GET"])
def get_shifts():
    # return events assigned to the current user (from token)
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify([])
    token = auth.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
    except Exception:
        return jsonify([])
    user_id = payload.get("sub")
    
    user_events = get_user_assigned_events(user_id)
    return jsonify(user_events)


@events_bp.route("/<event_id>/suggestions", methods=["GET"])
def get_assignment_suggestions(event_id):
    """
    Get AI-powered assignment suggestions for a shift
    
    Returns top 5 employee candidates with scores and reasoning
    
    Query params:
    - count: number of suggestions (default 5)
    """
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    # Get the shift/event
    shift = get_event_by_id(event_id)
    if not shift:
        return jsonify({"error": "Event not found"}), 404
    
    try:
        # Get all employees, events, and availabilities for algorithm
        employees = list_users()
        all_events = list_events()
        availabilities = list_availabilities()
        
        # Filter out any None values AND employees without IDs
        employees = [e for e in employees if e and e.get('id')]
        all_events = [e for e in all_events if e]
        availabilities = [a for a in availabilities if a]
        
        # Get count parameter
        count = request.args.get('count', 5, type=int)
        count = max(1, min(count, 30))  # Clamp between 1 and 30
        
        # Build current assignments dict (emp_id -> [shift_ids])
        # For MVP, assume no existing assignments yet
        current_assignments = {}
        
        # Get suggestions
        suggestions = suggest_assignments(
            shift,
            employees,
            all_events,
            availabilities,
            current_assignments,
            count=count
        )
        
        # Format response
        return jsonify({
            "shift_id": event_id,
            "shift_title": shift.get('title', 'Unknown'),
            "suggestions": suggestions,
            "count": len(suggestions)
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@events_bp.route("/<event_id>/autofill", methods=["POST"])
def autofill_shift(event_id):
    """
    Automatically assign employees to fill remaining shift slots
    
    Uses the greedy algorithm to select the best candidates and assigns them
    
    Returns:
    - List of newly assigned employees
    - Number of slots filled
    - Any errors if insufficient candidates
    """
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    company_id = session.get("company_id")
    
    # Get the shift/event
    shift = get_event_by_id(event_id)
    if not shift:
        return jsonify({"error": "Event not found"}), 404
    
    try:
        # Calculate slots to fill
        capacity = shift.get('capacity', 1)
        already_assigned = len(shift.get('assigned', []))
        slots_to_fill = max(0, capacity - already_assigned)
        
        if slots_to_fill == 0:
            return jsonify({
                "shift_id": event_id,
                "message": "Shift is already fully staffed",
                "capacity": capacity,
                "assigned": already_assigned,
                "newly_assigned": [],
                "count": 0,
                "errors": []
            }), 200
        
        # Prepare data for autofill
        employees, all_events, availabilities, valid_employee_ids, current_assignments = \
            prepare_autofill_data(company_id, shift)
        
        # Auto-assign using the algorithm
        assigned, errors = auto_assign_shift(
            shift,
            employees,
            all_events,
            availabilities,
            current_assignments,
            capacity_to_fill=slots_to_fill
        )
        
        # Check if we couldn't fill all slots
        slots_filled = len(assigned)
        slots_unfilled = slots_to_fill - slots_filled
        
        if slots_unfilled > 0 and not errors:
            errors.append(f"Could not fill {slots_unfilled} slot(s) - insufficient eligible employees available")
        
        # Actually assign them in the database
        newly_assigned = []
        valid_employee_ids = {e.get('id') for e in employees if e.get('id')}
        
        for emp_id in assigned:
            # STRICT validation: employee must be in our original employees list
            if emp_id not in valid_employee_ids:
                # Silently skip non-existent employees
                continue
            
            try:
                if assign_user_to_event(event_id, emp_id):
                    newly_assigned.append(emp_id)
            except Exception as e:
                # Log but continue with other assignments
                pass
        
        return jsonify({
            "shift_id": event_id,
            "shift_title": shift.get('title', 'Unknown'),
            "capacity": capacity,
            "previously_assigned": already_assigned,
            "slots_needed": slots_to_fill,
            "newly_assigned": newly_assigned,
            "count": len(newly_assigned),
            "slots_unfilled": max(0, slots_to_fill - len(newly_assigned)),
            "errors": errors if errors else []
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============ SHIFT SWAP ENDPOINTS ============

@events_bp.route("/swap/request", methods=["POST"])
def request_swap():
    """Request a shift swap with another employee"""
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json() or request.form
    
    user_id = session.get("user_id")
    target_id = data.get("target_employee_id")
    my_shift_id = data.get("initiator_shift_id") or data.get("my_shift_id")
    target_shift_id = data.get("target_shift_id")
    reason = data.get("reason", "")
    
    if not all([target_id, my_shift_id, target_shift_id]):
        return jsonify({
            "error": "Missing required fields",
            "status": "error",
            "received": {
                "target_employee_id": target_id,
                "initiator_shift_id": my_shift_id,
                "target_shift_id": target_shift_id
            }
        }), 400
    
    # Validate the swap
    company_id = session.get("company_id")
    all_events = list_events(company_id)
    validator = ShiftSwapValidator(all_events)
    is_valid, issues = validator.validate_swap(user_id, target_id, my_shift_id, target_shift_id)
    
    if not is_valid:
        return jsonify({
            "status": "error",
            "issues": issues
        }), 400
    
    # Create the request
    swap = create_shift_swap_request(user_id, target_id, my_shift_id, target_shift_id, reason)
    if swap:
        return jsonify({"status": "success", "message": "Swap request sent", "swap_id": swap.get('id')}), 201
    
    return jsonify({"status": "error", "error": "Failed to create swap"}), 500


@events_bp.route("/swaps/pending", methods=["GET"])
def get_pending_swaps():
    """Get pending swap requests for current user"""
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized", "swaps": []}), 401
    
    user_id = session.get("user_id")
    company_id = session.get("company_id")
    try:
        swaps = get_swap_requests(user_id, company_id)
        return jsonify({"swaps": swaps or []}), 200
    except Exception as e:
        print(f"Error getting swap requests: {e}")
        return jsonify({"swaps": [], "error": str(e)}), 200


@events_bp.route("/swap/<swap_id>/approve", methods=["POST"])
def approve_swap_endpoint(swap_id):
    """Approve a shift swap"""
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized", "status": "error"}), 401
    
    # Verify user is the target employee (the one approving)
    user_id = session.get("user_id")
    if not approve_shift_swap(swap_id, user_id):
        return jsonify({"status": "error", "message": "Failed to approve or unauthorized"}), 403
    
    return jsonify({"status": "success", "message": "Swap approved"}), 200


@events_bp.route("/swap/<swap_id>/reject", methods=["POST"])
def reject_swap_endpoint(swap_id):
    """Reject a shift swap"""
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized", "status": "error"}), 401
    
    # Verify user is the target employee (the one rejecting)
    user_id = session.get("user_id")
    if not reject_shift_swap(swap_id, user_id):
        return jsonify({"status": "error", "message": "Failed to reject or unauthorized"}), 403
    
    return jsonify({"status": "success", "message": "Swap rejected"}), 200


@events_bp.route("/api/employees", methods=["GET"])
def api_get_employees():
    """Get all employees in current company"""
    msg = f"[SWAP API] /api/employees called - session keys: {list(session.keys())}"
    print(msg, file=sys.stderr)
    sys.stderr.flush()
    
    if "user_id" not in session:
        print("[SWAP API] No user_id in session, returning 401", file=sys.stderr)
        sys.stderr.flush()
        return jsonify({"error": "Unauthorized", "employees": []}), 401
    
    company_id = session.get("company_id")
    user_id = session.get("user_id")
    msg = f"[SWAP API] company_id: {company_id}, user_id: {user_id}"
    print(msg, file=sys.stderr)
    sys.stderr.flush()
    
    try:
        employees = list_users(company_id)
        msg = f"[SWAP API] Found {len(employees)} total employees in company {company_id}"
        print(msg, file=sys.stderr)
        sys.stderr.flush()
    except Exception as e:
        msg = f"[SWAP API] Error getting employees: {e}"
        print(msg, file=sys.stderr)
        sys.stderr.flush()
        return jsonify({"error": str(e), "employees": [], "current_user_id": session.get("user_id")}), 500
    
    emp_list = []
    current_user = session.get("user_id")
    for e in employees:
        emp_id = e.get("id")
        if emp_id != current_user:
            emp_list.append({"id": emp_id, "name": format_employee_name(e)})
    
    result = {
        "current_user_id": session.get("user_id"),
        "employees": emp_list
    }
    return jsonify(result), 200


@events_bp.route("/api/employee/<employee_id>/shifts", methods=["GET"])
def api_get_employee_shifts(employee_id):
    """Get upcoming shifts for an employee"""
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    company_id = session.get("company_id")
    all_events = list_events(company_id)
    
    # Filter shifts assigned to this employee
    shifts = []
    for event in all_events:
        assigned = event.get("assigned", [])
        if isinstance(assigned, str):
            assigned = [s.strip() for s in assigned.split(",") if s.strip()]
        
        if employee_id in assigned:
            start_time, end_time = parse_shift_time(event)
            shifts.append({
                "id": event.get("id"),
                "title": event.get("title"),
                "start": event.get("start"),
                "end": event.get("end"),
                "start_time": start_time,
                "end_time": end_time
            })
    
    return jsonify({"shifts": shifts, "status": "success"})
