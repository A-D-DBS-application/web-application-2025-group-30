import os
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
