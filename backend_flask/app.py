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

from flask import Flask, jsonify, render_template, session, redirect, url_for, request
from controllers.auth import auth_bp
from controllers.users import users_bp
from controllers.events import events_bp
from controllers.availability import availability_bp
from models import get_user_by_id, list_events, list_users, get_availability_for_user, search_and_filter_events, calculate_statistics
from datetime import datetime, timedelta

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")

# Register Jinja filter for date formatting
def format_date(date_string):
    """Convert ISO date (2025-11-28) or ISO datetime to 'DD Mon YYYY' format"""
    try:
        # Handle both datetime and date strings
        date_part = date_string.split('T')[0] if 'T' in date_string else date_string
        dt = datetime.strptime(date_part, '%Y-%m-%d')
        return dt.strftime('%d %b %Y')
    except:
        return date_string

app.jinja_env.filters['format_date'] = format_date

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
    
    # Get user's availability windows
    my_availabilities = get_availability_for_user(str(user["id"]))
    
    # Separate past and upcoming shifts
    now = datetime.now()
    upcoming_shifts = []
    past_shifts = []
    
    for shift in my_shifts:
        try:
            shift_start = datetime.fromisoformat(shift.get('start', '').replace('Z', '+00:00'))
            if shift_start > now:
                upcoming_shifts.append(shift)
            else:
                past_shifts.append(shift)
        except:
            upcoming_shifts.append(shift)  # Default to upcoming if can't parse
    
    # Separate past and upcoming availability
    upcoming_availability = []
    past_availability = []
    
    for avail in my_availabilities:
        try:
            avail_start = datetime.fromisoformat(avail.get('start', '').replace('Z', '+00:00'))
            if avail_start > now:
                upcoming_availability.append(avail)
            else:
                past_availability.append(avail)
        except:
            upcoming_availability.append(avail)  # Default to upcoming if can't parse

    return render_template("employee.html", user=user, my_shifts=my_shifts, upcoming_shifts=upcoming_shifts, past_shifts=past_shifts, available_shifts=available_shifts, month=month, year=year, my_availabilities=my_availabilities, upcoming_availability=upcoming_availability, past_availability=past_availability)


@app.route("/manager")
def manager():
    if "user_id" not in session:
        return redirect(url_for("index"))
    
    user = get_user_by_id(session["user_id"])
    if not user or user.get("role") != "manager":
        return redirect(url_for("dashboard"))

    # Get month/year parameters or use current date
    month = request.args.get('month', type=int) or datetime.now().month
    year = request.args.get('year', type=int) or datetime.now().year

    all_events = list_events()
    all_users = list_users()
    # Filter to only employees
    employees = [u for u in all_users if u.get("role") == "employee"]
    
    # Get search and filter parameters from query string
    search_query = request.args.get('search', '')
    filter_understaffed = request.args.get('understaffed', '').lower() == 'true'
    filter_date_start = request.args.get('date_start', '')
    filter_date_end = request.args.get('date_end', '')
    
    # Apply search and filter
    filtered_events = search_and_filter_events(
        all_events,
        search_query=search_query,
        filter_understaffed=filter_understaffed,
        filter_date_start=filter_date_start,
        filter_date_end=filter_date_end
    )
    
    # Separate past and upcoming events
    now = datetime.now()
    upcoming_events = []
    past_events = []
    
    for event in filtered_events:
        try:
            event_start = datetime.fromisoformat(event.get('start', '').replace('Z', '+00:00'))
            if event_start > now:
                upcoming_events.append(event)
            else:
                past_events.append(event)
        except:
            upcoming_events.append(event)  # Default to upcoming if can't parse
    
    return render_template(
        "manager.html", 
        user=user, 
        events=filtered_events,
        upcoming_events=upcoming_events,
        past_events=past_events,
        all_events=all_events,
        employees=employees, 
        month=month, 
        year=year,
        search_query=search_query,
        filter_understaffed=filter_understaffed,
        filter_date_start=filter_date_start,
        filter_date_end=filter_date_end
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/statistics")
def statistics():
    if "user_id" not in session:
        return redirect(url_for("index"))
    
    user = get_user_by_id(session["user_id"])
    if not user or user.get("role") != "manager":
        return redirect(url_for("dashboard"))
    
    # Get all events and employees
    all_events = list_events()
    all_users = list_users()
    employees = [u for u in all_users if u.get("role") == "employee"]
    
    # Get all availabilities
    from models import list_availabilities
    all_availabilities = list_availabilities()
    
    # Get time period filter
    period = request.args.get('period', 'all')  # all, week, month
    
    # Filter events by time period based on scheduled start date
    filtered_events = all_events
    filtered_availabilities = all_availabilities
    
    if period != 'all':
        today = datetime.now()
        if period == 'week':
            week_start = today - timedelta(days=today.weekday())  # Start of current week
            week_end = week_start + timedelta(days=7)
            filtered_events = [
                e for e in all_events
                if week_start <= datetime.fromisoformat(e.get('start', '').replace('Z', '+00:00')) < week_end
            ]
            filtered_availabilities = [
                a for a in all_availabilities
                if week_start <= datetime.fromisoformat(a.get('start', '').replace('Z', '+00:00')) < week_end
            ]
        elif period == 'month':
            month_start = today.replace(day=1)
            if today.month == 12:
                month_end = month_start.replace(year=today.year + 1, month=1)
            else:
                month_end = month_start.replace(month=today.month + 1)
            filtered_events = [
                e for e in all_events
                if month_start <= datetime.fromisoformat(e.get('start', '').replace('Z', '+00:00')) < month_end
            ]
            filtered_availabilities = [
                a for a in all_availabilities
                if month_start <= datetime.fromisoformat(a.get('start', '').replace('Z', '+00:00')) < month_end
            ]
    
    # Calculate statistics
    stats = calculate_statistics(filtered_events, employees, filtered_availabilities)
    
    return render_template("statistics.html", user=user, stats=stats, period=period)


if __name__ == "__main__":
    # Development server
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
