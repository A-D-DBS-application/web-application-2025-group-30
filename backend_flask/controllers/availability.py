from flask import Blueprint, request, jsonify, session, redirect, url_for
import os
import jwt
from models import create_availability, list_availabilities, get_availability_for_user, get_user_by_id

availability_bp = Blueprint("availability", __name__)
SECRET = os.getenv("SECRET_KEY", "dev-secret")


@availability_bp.route("/submit", methods=["POST"])
def submit_availability():
    if "user_id" not in session:
        return redirect(url_for("index"))
        
    user_id = session["user_id"]
    data = request.form
    
    start = data.get("start")
    end = data.get("end")
    note = data.get("note", "")
    
    if start and end:
        create_availability(user_id, start, end, note)
        
    return redirect(url_for("dashboard"))


@availability_bp.route("/", methods=["GET"])
def list_avail():
    return jsonify(list_availabilities())


@availability_bp.route("/<user_id>", methods=["GET"])
def get_avail(user_id):
    return jsonify(get_availability_for_user(user_id))
