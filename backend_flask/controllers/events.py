from flask import Blueprint, request, jsonify, session, redirect, url_for
import os
import jwt
from models import create_event, list_events, assign_user_to_event, subscribe_user_to_event, confirm_user_assignment

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
    
    ok = assign_user_to_event(event_id, user_id)
    return redirect(url_for("manager"))


@events_bp.route("/<event_id>/confirm", methods=["POST"])
def confirm_event_subscription(event_id):
    if "user_id" not in session:
        return redirect(url_for("index"))

    user_id = request.form.get("user_id")
    if user_id:
        confirm_user_assignment(event_id, user_id)
        
    return redirect(url_for("manager"))


@events_bp.route("/<event_id>/subscribe", methods=["POST"])
def subscribe_event(event_id):
    if "user_id" not in session:
        return redirect(url_for("index"))
        
    user_id = session["user_id"]
    subscribe_user_to_event(event_id, user_id)
    
    return redirect(url_for("dashboard"))


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
