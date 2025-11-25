from flask import Blueprint, jsonify, request
import os
import jwt
from models import get_user_public, list_users, get_user_by_id

users_bp = Blueprint("users", __name__)
SECRET = os.getenv("SECRET_KEY", "dev-secret")


@users_bp.route("/", methods=["GET"])
def list_all_users():
    users = list_users()
    public = [get_user_public(u) for u in users]
    return jsonify(public)


@users_bp.route("/<user_id>", methods=["GET"])
def get_user(user_id):
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "not found"}), 404
    return jsonify(get_user_public(user))


@users_bp.route("/me", methods=["GET"])
def me():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"error": "missing token"}), 401
    token = auth.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
    except Exception:
        return jsonify({"error": "invalid token"}), 401
    user_id = payload.get("sub")
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "user not found"}), 404
    return jsonify(get_user_public(user))
