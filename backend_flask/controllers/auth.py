import os
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template
import jwt
import bcrypt
from models import create_user, find_user_by_username, get_user_public

auth_bp = Blueprint("auth", __name__)
SECRET = os.getenv("SECRET_KEY", "dev-secret")
ALGORITHM = "HS256"

@auth_bp.route("/register", methods=["POST"])
def register():
    # Support both JSON and Form data
    data = request.get_json(silent=True) or request.form
    username = data.get("username")
    role = data.get("role", "employee")
    
    if not username:
        return render_template("login.html", error="Username required")
        
    if find_user_by_username(username):
        return render_template("login.html", error="User exists")
        
    # No password required for registration; store empty password
    user = create_user(username, "", role)
    
    # Auto login
    session["user_id"] = user["id"]
    session["user_role"] = role
    
    if role == "manager":
        return redirect(url_for("manager"))
    return redirect(url_for("dashboard"))

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or request.form
    username = data.get("username")
    
    if not username:
        return render_template("login.html", error="Username required")
        
    user = find_user_by_username(username)
    if not user:
        return render_template("login.html", error="Invalid credentials")
        
    session["user_id"] = user["id"]
    session["user_role"] = user.get("role", "employee")
    
    if user.get("role") == "manager":
        return redirect(url_for("manager"))
    return redirect(url_for("dashboard"))

