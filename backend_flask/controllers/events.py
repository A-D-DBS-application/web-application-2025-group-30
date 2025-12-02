from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template, flash
import os
import sys
import jwt
from models import create_event, list_events, assign_user_to_event, subscribe_user_to_event, confirm_user_assignment, get_event_by_id, delete_event, update_event

# Import conflict detection algorithm
algoritme_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Flask', 'app'))
if algoritme_path not in sys.path:
    sys.path.insert(0, algoritme_path)

try:
    from algoritme1 import validate_assignment
    print("✓ Conflict detection algorithm loaded successfully")
except ImportError as e:
    print(f"✗ Failed to import algoritme1: {e}")
    # Fallback if import fails - ALLOW all assignments (no conflict checking)
    def validate_assignment(employee_id, event, all_events, min_break_hours=8.0, max_daily_hours=12.0):
        return True, []

events_bp = Blueprint("events", __name__)
SECRET = os.getenv("SECRET_KEY", "dev-secret")


@events_bp.route("/", methods=["GET"])
def get_events():
    return jsonify(list_events())


@events_bp.route("/create", methods=["POST"])
def create_new_event():
    if "user_id" not in session:
        return redirect(url_for("index"))
        
    data = request.form
    # description is optional in code but UI will send it
    # Combine date and time if separate
    event_data = dict(data)
    
    if "date" in data and "start_time" in data:
        event_data["start"] = f"{data['date']}T{data['start_time']}"
    if "date" in data and "end_time" in data:
        event_data["end"] = f"{data['date']}T{data['end_time']}"
        
    create_event(event_data)
    return redirect(url_for("manager"))


@events_bp.route("/<event_id>/assign", methods=["POST"])
def assign_event(event_id):
    if "user_id" not in session:
        return redirect(url_for("index"))
    
    # Support both JSON and Form data for direct manager assignment
    data = request.get_json(silent=True) or request.form
    user_id = data.get("user_id")
    if not user_id:
        return redirect(url_for("manager"))
    
    # Check for conflicts before assigning
    current_event = get_event_by_id(event_id)
    all_events = list_events()
    
    if current_event:
        # Detailed logging
        print(f"\n{'='*60}")
        print(f"CONFLICT CHECK: Assigning user {user_id[:8]}... to event '{current_event.get('title')}'")
        print(f"Event details:")
        print(f"  ID: {current_event.get('id')}")
        print(f"  Start: {current_event.get('start')}")
        print(f"  End: {current_event.get('end')}")
        print(f"  Location: {current_event.get('location')}")
        print(f"  Currently assigned: {current_event.get('assigned', [])}")
        
        # Show all events this employee is currently in
        employee_events = [e for e in all_events if user_id in e.get('assigned', [])]
        print(f"\nEmployee currently assigned to {len(employee_events)} events:")
        for e in employee_events:
            print(f"  - '{e.get('title')}' at {e.get('location')} ({e.get('start')} to {e.get('end')})")
        
        print(f"\nCalling validate_assignment...")
        is_valid, conflicts = validate_assignment(user_id, current_event, all_events)
        
        print(f"Result: valid={is_valid}, conflicts={len(conflicts)}")
        if conflicts:
            for c in conflicts:
                print(f"  Conflict: {c}")
        print(f"{'='*60}\n")
        
        if not is_valid:
            # Format conflict messages for display
            conflict_msgs = []
            for conflict in conflicts:
                if conflict['severity'] == 'error':
                    conflict_msgs.append(f"❌ {conflict['message']}")
                else:
                    conflict_msgs.append(f"⚠️ {conflict['message']}")
            
            flash("Cannot assign employee due to conflicts: " + " | ".join(conflict_msgs), "error")
            return redirect(url_for("manager"))
    
    ok = assign_user_to_event(event_id, user_id)
    if ok:
        flash("Employee assigned successfully!", "success")
    return redirect(url_for("manager"))


@events_bp.route("/<event_id>/confirm", methods=["POST"])
def confirm_event_subscription(event_id):
    if "user_id" not in session:
        return redirect(url_for("index"))

    user_id = request.form.get("user_id")
    if user_id:
        # Check for conflicts before confirming pending assignment
        current_event = get_event_by_id(event_id)
        all_events = list_events()
        
        if current_event:
            is_valid, conflicts = validate_assignment(user_id, current_event, all_events)
            
            if not is_valid:
                # Format conflict messages for display
                conflict_msgs = []
                for conflict in conflicts:
                    if conflict['severity'] == 'error':
                        conflict_msgs.append(f"❌ {conflict['message']}")
                    else:
                        conflict_msgs.append(f"⚠️ {conflict['message']}")
                
                flash("Cannot confirm assignment due to conflicts: " + " | ".join(conflict_msgs), "error")
                return redirect(url_for("manager"))
        
        confirm_user_assignment(event_id, user_id)
        flash("Assignment confirmed successfully!", "success")
        
    return redirect(url_for("manager"))


@events_bp.route("/<event_id>/subscribe", methods=["POST"])
def subscribe_event(event_id):
    if "user_id" not in session:
        return redirect(url_for("index"))
        
    user_id = session["user_id"]
    subscribe_user_to_event(event_id, user_id)
    
    return redirect(url_for("dashboard"))


@events_bp.route("/<event_id>/delete", methods=["POST"])
def delete_event_route(event_id):
    if "user_id" not in session:
        return redirect(url_for("index"))
    
    delete_event(event_id)
    return redirect(url_for("manager"))


@events_bp.route("/<event_id>/edit", methods=["GET"])
def edit_event_form(event_id):
    if "user_id" not in session:
        return redirect(url_for("index"))
    
    event = get_event_by_id(event_id)
    if not event:
        return redirect(url_for("manager"))
    
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
    return redirect(url_for("manager"))


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
    all_events = list_events()
    user_events = [e for e in all_events if user_id in (e.get("assigned") or [])]
    return jsonify(user_events)
