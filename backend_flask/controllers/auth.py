import os
from flask import Blueprint, request, render_template, session, redirect, url_for
from models import (
    create_user, 
    find_user_by_username, 
    validate_registration_code,
    get_company_by_code,
    create_company,
    list_companies,
    update_company_owner
)

auth_bp = Blueprint("auth", __name__)
SECRET = os.getenv("SECRET_KEY", "dev-secret")

@auth_bp.route("/register", methods=["POST"])
def register():
    # Support both JSON and Form data
    data = request.get_json(silent=True) or request.form
    username = data.get("username")
    role = data.get("role", "employee")
    registration_code = data.get("registration_code", "").strip().upper()
    company_name = data.get("company_name", "").strip()
    
    if not username:
        return render_template("login.html", error="Username required")
        
    if find_user_by_username(username):
        return render_template("login.html", error="User already exists")
    
    company_id = None
    
    # Check if registration code is provided
    if registration_code:
        # Validate the code
        is_valid, error_msg = validate_registration_code(registration_code)
        if not is_valid:
            return render_template("login.html", error=error_msg)
        
        # Get company by code
        company = get_company_by_code(registration_code)
        if company:
            company_id = company.get("id")
    else:
        # No code provided
        if role == "manager":
            # Managers can create a NEW company without code
            if not company_name:
                company_name = f"{username}'s Company"
            new_company = create_company(company_name)
            company_id = new_company.get("id")
        else:
            # Employees MUST provide a code
            existing_companies = list_companies()
            if existing_companies:
                # Companies exist but no code provided for employee
                return render_template("login.html", error="Registration code required for employees")
            else:
                # This is the very first user (employee without code) - create company
                company_name = f"{username}'s Company"
                new_company = create_company(company_name)
                company_id = new_company.get("id")
    
    # Create user with company_id
    user = create_user(username, "", role, company_id=company_id)
    
    # If this is a manager and first user of that company, set as owner
    if role == "manager" and company_id:
        try:
            update_company_owner(company_id, user["id"])
        except:
            pass  # Fallback if owner update fails
    
    # Auto login - include company_id for multi-tenant support
    session["user_id"] = user["id"]
    session["user_role"] = role
    session["user_name"] = username
    if user.get("company_id"):
        session["company_id"] = user["company_id"]
    
    if role == "manager":
        return redirect(url_for("main.manager"))
    return redirect(url_for("main.dashboard"))

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or request.form
    username = data.get("username")
    
    if not username:
        return render_template("login.html", error="Username required")
        
    user = find_user_by_username(username)
    if not user:
        return render_template("login.html", error="Invalid credentials")
        
    # Login - include company_id for multi-tenant support
    session["user_id"] = user["id"]
    session["user_role"] = user.get("role", "employee")
    session["user_name"] = user.get("username", username)
    if user.get("company_id"):
        session["company_id"] = user["company_id"]
    
    if user.get("role") == "manager":
        return redirect(url_for("main.manager"))
    return redirect(url_for("main.dashboard"))

