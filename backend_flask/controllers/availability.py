from flask import Blueprint, request, jsonify
import os
import jwt
from models import create_availability, list_availabilities, get_availability_for_user

availability_bp = Blueprint("availability", __name__)
SECRET = os.getenv("SECRET_KEY", "dev-secret")


@availability_bp.route("/", methods=["POST"])
def submit_availability():
    data = request.get_json() or {}
    user_id = data.get("user_id")
    # try to get from token if not provided
    auth = request.headers.get("Authorization", "")
    if not user_id and auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, SECRET, algorithms=["HS256"])
            user_id = payload.get("sub")
        except Exception:
            pass
    if not user_id:
        return jsonify({"error": "user_id required"}), 400
    start = data.get("start")
    end = data.get("end")
    note = data.get("note", "")
    if not start or not end:
        return jsonify({"error": "start and end required"}), 400
    rec = create_availability(user_id, start, end, note)
    return jsonify(rec), 201


@availability_bp.route("/", methods=["GET"])
def list_avail():
    return jsonify(list_availabilities())


@availability_bp.route("/<user_id>", methods=["GET"])
def get_avail(user_id):
    return jsonify(get_availability_for_user(user_id))
