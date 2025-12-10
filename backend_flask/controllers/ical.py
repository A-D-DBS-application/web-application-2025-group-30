from flask import Blueprint, request, redirect, url_for, flash, session, Response
from icalendar import Calendar, Event
from datetime import datetime
from models import create_event, get_user_by_id, list_events, get_assigned_users_for_event
import os

ical_bp = Blueprint("ical", __name__, url_prefix="/ical")

@ical_bp.route("/import", methods=["POST"])
def import_ical():
    """Import events from an iCal (.ics) file"""
    if "user_id" not in session:
        return redirect(url_for("index"))
    
    # Check if user is a manager
    from models import get_user_by_id
    user = get_user_by_id(session["user_id"])
    if not user or user.get("role") != "manager":
        flash("Only managers can import calendars", "error")
        return redirect(url_for("dashboard"))
    
    # Check if file was provided
    if 'calendar_file' not in request.files:
        flash("No file provided", "error")
        return redirect(url_for("manager"))
    
    file = request.files['calendar_file']
    if file.filename == '':
        flash("No file selected", "error")
        return redirect(url_for("manager"))
    
    if not file.filename.endswith('.ics'):
        flash("File must be in .ics format", "error")
        return redirect(url_for("manager"))
    
    try:
        # Parse iCal file
        cal_content = file.read()
        cal = Calendar.from_ical(cal_content)
        
        imported_count = 0
        errors = []
        
        # Extract events from calendar
        for component in cal.walk():
            if component.name == "VEVENT":
                try:
                    # Extract event details
                    summary = str(component.get('summary', 'Untitled Event'))
                    description = str(component.get('description', ''))
                    location = str(component.get('location', ''))
                    
                    # Get start and end times
                    dtstart = component.get('dtstart')
                    dtend = component.get('dtend')
                    
                    if not dtstart or not dtend:
                        errors.append(f"Event '{summary}' missing start or end time")
                        continue
                    
                    # Convert to ISO format strings
                    start_dt = dtstart.dt
                    end_dt = dtend.dt
                    
                    # Handle both date and datetime objects
                    if hasattr(start_dt, 'isoformat'):
                        start_str = start_dt.isoformat()
                    else:
                        start_str = datetime.combine(start_dt, datetime.min.time()).isoformat()
                    
                    if hasattr(end_dt, 'isoformat'):
                        end_str = end_dt.isoformat()
                    else:
                        end_str = datetime.combine(end_dt, datetime.min.time()).isoformat()
                    
                    # Create event with default capacity
                    event_data = {
                        "title": summary,
                        "description": description,
                        "start": start_str,
                        "end": end_str,
                        "location": location,
                        "capacity": 10,  # Default capacity - can be customized
                        "type": "shift"
                    }
                    
                    create_event(**event_data)
                    imported_count += 1
                
                except Exception as e:
                    errors.append(f"Error importing event: {str(e)}")
        
        # Provide feedback
        if imported_count > 0:
            flash(f"Successfully imported {imported_count} event(s)", "success")
        
        if errors:
            for error in errors:
                flash(error, "warning")
        
        if imported_count == 0 and errors:
            flash("No events were imported", "error")
        
        return redirect(url_for("manager"))
    
    except Exception as e:
        flash(f"Error reading iCal file: {str(e)}", "error")
        return redirect(url_for("manager"))

@ical_bp.route("/feed/<token>")
def calendar_feed(token):
    """Generate iCal feed for employee's assigned shifts"""
    try:
        # Verify token format (basic security)
        # In production, you'd store/validate these tokens properly
        user = get_user_by_id(token)
        if not user:
            return Response("Unauthorized", status=401)
        
        # Create calendar
        cal = Calendar()
        cal.add('prodid', '-//Personnel Scheduler//EN')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'PUBLISH')
        cal.add('x-wr-calname', f"{user.get('username', 'Employee')} - Shifts")
        cal.add('x-wr-caldesc', 'Your assigned shifts')
        cal.add('x-wr-timezone', 'UTC')
        
        # Get all events
        all_events = list_events()
        
        # Filter to only events assigned to this user
        user_id = token  # Token is the user ID
        for event in all_events:
            assigned_users = get_assigned_users_for_event(event["id"])
            if user_id in assigned_users:
                # Create iCal event
                ical_event = Event()
                ical_event.add('summary', event.get('title', 'Shift'))
                ical_event.add('description', event.get('description', ''))
                ical_event.add('location', event.get('location', ''))
                
                # Parse ISO datetime strings
                try:
                    start = datetime.fromisoformat(event.get('start', '').replace('Z', '+00:00'))
                    end = datetime.fromisoformat(event.get('end', '').replace('Z', '+00:00'))
                    ical_event.add('dtstart', start)
                    ical_event.add('dtend', end)
                except:
                    continue  # Skip events with invalid dates
                
                # Add unique ID
                ical_event.add('uid', f"{event['id']}@personnel-scheduler")
                ical_event.add('created', datetime.now())
                ical_event.add('last-modified', datetime.now())
                
                # Add event to calendar
                cal.add_component(ical_event)
        
        # Return as iCal file
        response = Response(cal.to_ical(), mimetype='text/calendar')
        response.headers['Content-Disposition'] = f'attachment; filename="shifts.ics"'
        return response
    
    except Exception as e:
        return Response(f"Error generating calendar: {str(e)}", status=500)

@ical_bp.route("/subscribe")
def subscribe_info():
    """Show calendar subscription instructions"""
    if "user_id" not in session:
        return redirect(url_for("index"))
    
    user = get_user_by_id(session["user_id"])
    if not user:
        return redirect(url_for("index"))
    
    # Generate feed URL
    feed_url = f"{request.host_url.rstrip('/')}/ical/feed/{user['id']}"
    
    return {
        "feed_url": feed_url,
        "username": user.get('username'),
        "instructions": {
            "google_calendar": "Go to Settings > Add calendar > Subscribe to calendar > paste the URL",
            "outlook": "Go to Add calendar > Subscribe from web > paste the URL",
            "apple_calendar": "File > New Calendar Subscription > paste the URL"
        }
    }

