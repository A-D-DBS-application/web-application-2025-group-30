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

from flask import Flask, jsonify, render_template
from controllers.auth import auth_bp
from controllers.users import users_bp
from controllers.events import events_bp
from controllers.availability import availability_bp

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")

# Register blueprints
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(users_bp, url_prefix="/users")
app.register_blueprint(events_bp, url_prefix="/events")
app.register_blueprint(availability_bp, url_prefix="/availability")


@app.route("/")
def index():
    # Serve the login page (vanilla HTML/JS)
    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/manager")
def manager():
    return render_template("manager.html")


if __name__ == "__main__":
    # Development server
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
