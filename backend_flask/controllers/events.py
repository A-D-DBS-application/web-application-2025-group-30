from flask import Blueprint, request, jsonify
import os
import jwt
from models import create_event, list_events, EVENTS, assign_user_to_event, subscribe_user_to_event, confirm_user_assignment

events_bp = Blueprint("events", __name__)
SECRET = os.getenv("SECRET_KEY", "dev-secret")


@events_bp.route("/", methods=["GET"])
def get_events():
    return jsonify(list_events())


@events_bp.route("/", methods=["POST"])
def create_new_event():
    data = request.get_json() or {}
    # description is optional in code but UI will send it
    required = ["title", "start", "end", "capacity"]
    for r in required:
        if r not in data:
            return jsonify({"error": f"{r} required"}), 400
    event = create_event(data)
    return jsonify(event), 201


@events_bp.route("/<event_id>/assign", methods=["POST"])
def assign_event(event_id):
    body = request.get_json() or {}
    user_id = body.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id required"}), 400
    ok = assign_user_to_event(event_id, user_id)
    if not ok:
        return jsonify({"error": "cannot assign (not found or full)"}), 400
    return jsonify({"ok": True})


@events_bp.route("/<event_id>/confirm", methods=["POST"])
def confirm_event_subscription(event_id):
    body = request.get_json() or {}
    user_id = body.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id required"}), 400
    ok = confirm_user_assignment(event_id, user_id)
    if not ok:
        return jsonify({"error": "cannot confirm (not found or full)"}), 400
    return jsonify({"ok": True})


@events_bp.route("/<event_id>/subscribe", methods=["POST"])
def subscribe_event(event_id):
    # subscribe the calling user to an event (use token)
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"error": "missing token"}), 401
    token = auth.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
    except Exception:
        return jsonify({"error": "invalid token"}), 401
    user_id = payload.get("sub")
    ok = subscribe_user_to_event(event_id, user_id)
    if not ok:
        return jsonify({"error": "cannot subscribe (full or not found)"}), 400
    return jsonify({"ok": True})


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
    user_events = [e for e in EVENTS.values() if user_id in e.get("assigned", [])]
    return jsonify(user_events)
