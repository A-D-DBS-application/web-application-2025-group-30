"""
Centralized routes for multi-tenant application.
All routes include company_id isolation for data security.
"""

from flask import Blueprint, render_template, session, redirect, url_for, request
from models import (
    get_user_by_id, 
    list_events, 
    list_users, 
    get_availability_for_user,
    search_and_filter_events, 
    calculate_statistics,
    list_availabilities,
    get_company_by_id
)
from datetime import datetime, timedelta, timezone

# Create main blueprint
main_bp = Blueprint("main", __name__)


def get_company_id():
    """Get company_id from session, or None if not logged in"""
    if "company_id" not in session:
        return None
    return session["company_id"]


def require_login(f):
    """Decorator to require login"""
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper


def require_manager(f):
    """Decorator to require manager role"""
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("main.index"))
        
        user = get_user_by_id(session["user_id"])
        if not user or user.get("role") != "manager":
            return redirect(url_for("main.dashboard"))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper


@main_bp.route("/")
def index():
    """Login/Register page or redirect if already logged in"""
    if "user_id" in session:
        try:
            user = get_user_by_id(session["user_id"])
            if user:
                if user.get("role") == "manager":
                    return redirect(url_for("main.manager"))
                return redirect(url_for("main.dashboard"))
        except Exception:
            session.clear()
    
    return render_template("login.html")


@main_bp.route("/dashboard")
@require_login
def dashboard():
    """Employee dashboard - shows shifts and availability for their company"""
    user = get_user_by_id(session["user_id"])
    if not user:
        session.clear()
        return redirect(url_for("main.index"))
    
    company_id = user.get("company_id")
    if not company_id:
        session.clear()
        return redirect(url_for("main.index"))
    
    # Get month/year parameters
    month = request.args.get('month', type=int) or datetime.now().month
    year = request.args.get('year', type=int) or datetime.now().year
    
    # Get ONLY this company's events
    all_events = list_events(company_id)
    my_shifts = [e for e in all_events if user["id"] in (e.get("assigned") or [])]
    
    available_shifts = []
    for e in all_events:
        if user["id"] not in (e.get("assigned") or []):
            available_shifts.append(e)
    
    # Get user's availability windows
    my_availabilities = get_availability_for_user(str(user["id"]))
    
    # Separate past and upcoming
    now = datetime.now(timezone.utc)
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
            upcoming_shifts.append(shift)
    
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
            upcoming_availability.append(avail)
    
    # Get company name
    company = get_company_by_id(company_id)
    company_name = company.get("name") if company else "Company"
    
    return render_template(
        "employee.html",
        user=user,
        my_shifts=my_shifts,
        upcoming_shifts=upcoming_shifts,
        past_shifts=past_shifts,
        available_shifts=available_shifts,
        month=month,
        year=year,
        my_availabilities=my_availabilities,
        upcoming_availability=upcoming_availability,
        past_availability=past_availability,
        company_name=company_name
    )


@main_bp.route("/manager")
@require_manager
def manager():
    """Manager dashboard - shows events, employees, and availabilities for their company"""
    user = get_user_by_id(session["user_id"])
    company_id = user.get("company_id")
    
    # Get month/year parameters
    month = request.args.get('month', type=int) or datetime.now().month
    year = request.args.get('year', type=int) or datetime.now().year
    
    # Get ONLY this company's data
    all_events = list_events(company_id)
    all_users = list_users(company_id)
    employees = [u for u in all_users if u.get("role") == "employee"]
    
    # Get search/filter parameters
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
    
    # Separate past and upcoming
    now = datetime.now(timezone.utc)
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
            upcoming_events.append(event)
    
    # Get company code for inviting employees
    company = get_company_by_id(company_id)
    company_code = company.get("registration_code") if company else None
    company_name = company.get("name") if company else "Company"
    
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
        filter_date_end=filter_date_end,
        company_code=company_code,
        company_name=company_name
    )


@main_bp.route("/statistics")
@require_manager
def statistics():
    """Statistics page - shows stats for company"""
    user = get_user_by_id(session["user_id"])
    company_id = user.get("company_id")
    
    # Get ONLY this company's data
    all_events = list_events(company_id)
    all_users = list_users(company_id)
    employees = [u for u in all_users if u.get("role") == "employee"]
    all_availabilities = list_availabilities(company_id)
    
    # Get time period filter
    period = request.args.get('period', 'all')
    
    # Filter by time period
    filtered_events = all_events
    filtered_availabilities = all_availabilities
    
    if period != 'all':
        today = datetime.now(timezone.utc)
        if period == 'week':
            week_start = today - timedelta(days=today.weekday())
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


@main_bp.route("/logout")
def logout():
    """Logout - clear session"""
    session.clear()
    return redirect(url_for("main.index"))
