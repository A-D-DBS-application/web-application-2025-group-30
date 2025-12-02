import os
from flask import Flask, jsonify, render_template, session, redirect, url_for, request
from controllers.auth import auth_bp
from controllers.users import users_bp
from controllers.events import events_bp
from controllers.availability import availability_bp
from models import get_user_by_id, list_events, list_users

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")

# Register blueprints
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(users_bp, url_prefix="/users")
app.register_blueprint(events_bp, url_prefix="/events")
app.register_blueprint(availability_bp, url_prefix="/availability")


@app.route("/")
def index():
    if "user_id" in session:
        try:
            user = get_user_by_id(session["user_id"])
            if user:
                if user.get("role") == "manager":
                    return redirect(url_for("manager"))
                return redirect(url_for("dashboard"))
        except Exception:
            # If DB is down or table missing, clear session to avoid crash loop
            session.clear()
            
    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("index"))
    
    user = get_user_by_id(session["user_id"])
    if not user:
        session.clear()
        return redirect(url_for("index"))

    # Get month/year parameters or use current date
    from datetime import datetime
    month = request.args.get('month', type=int) or datetime.now().month
    year = request.args.get('year', type=int) or datetime.now().year

    # Prepare data for the template
    all_events = list_events()
    my_shifts = [e for e in all_events if user["id"] in (e.get("assigned") or [])]
    
    available_shifts = []
    for e in all_events:
        if user["id"] not in (e.get("assigned") or []):
            available_shifts.append(e)

    return render_template("dashboard.html", user=user, my_shifts=my_shifts, available_shifts=available_shifts, month=month, year=year)


@app.route("/manager")
def manager():
    if "user_id" not in session:
        return redirect(url_for("index"))
    
    user = get_user_by_id(session["user_id"])
    if not user or user.get("role") != "manager":
        return redirect(url_for("dashboard"))

    # Get month/year parameters or use current date
    from datetime import datetime
    month = request.args.get('month', type=int) or datetime.now().month
    year = request.args.get('year', type=int) or datetime.now().year

    all_events = list_events()
    all_users = list_users()
    # Filter to only employees
    employees = [u for u in all_users if u.get("role") == "employee"]
    return render_template("manager.html", user=user, events=all_events, employees=employees, month=month, year=year)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    # Development server
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
