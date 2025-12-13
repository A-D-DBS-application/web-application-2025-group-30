import os
from flask import Flask, jsonify, render_template, session, redirect, url_for, request
from migrations import run_migrations
from routes import main_bp
from controllers.auth import auth_bp
from controllers.users import users_bp
from controllers.events import events_bp
from controllers.availability import availability_bp
from controllers.ical import ical_bp
from models import get_user_by_id, list_events, list_users, get_availability_for_user, search_and_filter_events, calculate_statistics
from datetime import datetime, timedelta, timezone

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
# Main routes (dashboard, manager, statistics, logout)
app.register_blueprint(main_bp)

# API blueprints
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(users_bp, url_prefix="/users")
app.register_blueprint(events_bp, url_prefix="/events")
app.register_blueprint(availability_bp, url_prefix="/availability")
app.register_blueprint(ical_bp, url_prefix="/ical")

# Run migrations on startup
run_migrations()

if __name__ == "__main__":
    # Development server
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
