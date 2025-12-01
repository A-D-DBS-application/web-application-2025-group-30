import os
import importlib.util as _importlib_util
import pkgutil as _pkgutil

# Python 3.12+ removed `pkgutil.get_loader`. Flask's package-finding
# code still calls it, so provide a small compatibility shim that
# returns an object with the attributes Flask expects.
if not hasattr(_pkgutil, "get_loader"):
    def _get_loader(name):
        try:
            spec = _importlib_util.find_spec(name)
        except (ImportError, ValueError):
            return None
        if spec is None:
            return None

        class _CompatLoader:
            def __init__(self, spec):
                self._spec = spec
                # some loaders expose an `archive` attribute (zipimport).
                self.archive = None

            def get_filename(self, mod_name):
                return self._spec.origin

            def is_package(self, mod_name):
                return bool(self._spec.submodule_search_locations)

        return _CompatLoader(spec)

    _pkgutil.get_loader = _get_loader

from flask import Flask, jsonify, render_template, session, redirect, url_for
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

    # Prepare data for the template
    all_events = list_events()
    my_shifts = [e for e in all_events if user["id"] in (e.get("assigned") or [])]
    
    available_shifts = []
    for e in all_events:
        if user["id"] not in (e.get("assigned") or []):
            available_shifts.append(e)

    return render_template("dashboard.html", user=user, my_shifts=my_shifts, available_shifts=available_shifts)


@app.route("/manager")
def manager():
    if "user_id" not in session:
        return redirect(url_for("index"))
    
    user = get_user_by_id(session["user_id"])
    if not user or user.get("role") != "manager":
        return redirect(url_for("dashboard"))

    all_events = list_events()
    all_users = list_users()
    # Filter to only employees
    employees = [u for u in all_users if u.get("role") == "employee"]
    return render_template("manager.html", user=user, events=all_events, employees=employees)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    # Development server
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
