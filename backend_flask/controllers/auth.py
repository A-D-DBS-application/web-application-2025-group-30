import os
from flask import Blueprint, request, jsonify
import jwt
import bcrypt
from models import create_user, find_user_by_username, get_user_public

auth_bp = Blueprint("auth", __name__)
SECRET = os.getenv("SECRET_KEY", "dev-secret")
ALGORITHM = "HS256"

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username")
    role = data.get("role", "employee")
    if not username:
        return jsonify({"error": "username required"}), 400
    if find_user_by_username(username):
        return jsonify({"error": "user exists"}), 400
    # No password required for registration; store empty password
    user = create_user(username, "", role)
    return jsonify(get_user_public(user)), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = data.get("username")
    if not username:
        return jsonify({"error": "username required"}), 400
    user = find_user_by_username(username)
    if not user:
        return jsonify({"error": "invalid credentials"}), 401
    token = jwt.encode({"sub": user["id"]}, SECRET, algorithm=ALGORITHM)
    return jsonify({"access_token": token, "token_type": "bearer"})
