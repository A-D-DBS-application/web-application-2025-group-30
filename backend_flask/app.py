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
from migrations import run_migrations
from routes.main import main_bp
from routes.auth import auth_bp
from routes.users import users_bp
from routes.events import events_bp
from routes.availability import availability_bp
from routes.ical import ical_bp
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
