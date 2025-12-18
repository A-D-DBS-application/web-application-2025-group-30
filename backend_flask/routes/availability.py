from flask import Blueprint, request, jsonify, session, redirect, url_for
import os
import jwt
from models import create_availability, list_availabilities, get_availability_for_user, get_user_by_id, delete_availability_for_user

availability_bp = Blueprint("availability", __name__)
SECRET = os.getenv("SECRET_KEY", "dev-secret")


@availability_bp.route("/submit", methods=["POST"])
def submit_availability():
    if "user_id" not in session:
        return redirect(url_for("main.index"))
        
    user_id = session["user_id"]
    
    # Get company_id from the user
    user = get_user_by_id(user_id)
    if not user:
        return redirect(url_for("main.index"))
    
    company_id = user.get("company_id")
    
    # Delete all previous availability entries for this user (to avoid duplicates)
    delete_availability_for_user(user_id, company_id)
    
    data = request.form
    
    always_available = data.get("always_available") == "true"
    
    if always_available:
        # For "always available", create an entry that spans 1 month
        # This makes the employee available for any shift within that period
        from datetime import datetime, timedelta
        start = datetime.now().isoformat()
        end = (datetime.now() + timedelta(days=30)).isoformat()  # 1 month ahead
        note = data.get("note", "Always available")
        if note and note != "":
            note = f"Always available - {note}"
        else:
            note = "Always available"
        create_availability(user_id, start, end, note, company_id)
    else:
        start = data.get("start")
        end = data.get("end")
        note = data.get("note", "")
        
        if not start or not end:
            # If unchecking "always available" without providing new times,
            # just delete all availabilities (removes "always available" status)
            return redirect(url_for("main.dashboard"))
        
        create_availability(user_id, start, end, note, company_id)
        
    return redirect(url_for("main.dashboard"))


@availability_bp.route("/", methods=["GET"])
def list_avail():
    return jsonify(list_availabilities())


@availability_bp.route("/<user_id>", methods=["GET"])
def get_avail(user_id):
    return jsonify(get_availability_for_user(user_id))
