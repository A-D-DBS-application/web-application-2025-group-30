import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# -------------------------------------------------
# 1. Config & Supabase client
# -------------------------------------------------

# Pad naar de projectroot (één niveau boven de Flask-map)
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SUPABASE_URL = os.getenv("https://rflzgpbuvokvlzaqrige.supabase.co")
SUPABASE_KEY = os.getenv("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJmbHpncGJ1dm9rdmx6YXFyaWdlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA4OTQwMDUsImV4cCI6MjA3NjQ3MDAwNX0.g_-QLpllGBnZDfQ51oUtN8FYhAWQASfJCgOkY1-jMoY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL of SUPABASE_KEY ontbreekt in venv")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)
app.secret_key = os.getenv("Groep30", "dev-secret-key")  # voor flash() etc.


# -------------------------------------------------
# 2. Registratie-route
# -------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        # Toon gewoon het formulier
        return render_template("register.html")

    # POST: formulier verwerkt
    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    # Eenvoudige validatie
    if not full_name or not email or not password:
        flash("Alle velden zijn verplicht.", "error")
        return render_template("register.html", full_name=full_name, email=email)

    try:
        # 1) User aanmaken in Supabase Auth (auth.users)
        #    Dit beheert wachtwoord, login, beveiliging, enz.
        auth_response = supabase.auth.sign_up(
            {
                "email": email,
                "password": password,
                # optioneel extra metadata:
                "options": {
                    "data": {
                        "full_name": full_name
                    }
                }
            }
        )

        user = auth_response.user
        if user is None:
            flash("Registratie mislukt (geen user-object teruggekregen).", "error")
            return render_template("register.html", full_name=full_name, email=email)

        user_id = user.id  # <-- unieke user-id van Supabase Auth

        # 2) Profiel-record aanmaken in onze eigen 'profiles'-tabel
        #    Hier slaan we extra gegevens op, inclusief dezelfde user_id
        profile_data = {
            "id": user_id,        # moet overeenkomen met 'profiles.id' (uuid)
            "full_name": full_name,
        }

        db_response = supabase.table("profiles").insert(profile_data).execute()

        # Je kan db_response inspecteren bij debugging:
        # print(db_response)

        flash("Registratie succesvol! Je kan nu inloggen.", "success")
        return redirect(url_for("register_success"))

    except Exception as e:
        # In een echte app zou je dit loggen met logging i.p.v. print
        print("Fout bij registratie:", str(e))
        flash(f"Er ging iets mis bij de registratie: {e}", "error")
        return render_template("register.html", full_name=full_name, email=email)


@app.route("/register/success")
def register_success():
    return "<h1>Registratie gelukt!</h1><p>Je account is aangemaakt.</p>"


if __name__ == "__main__":
    app.run(debug=True)




# 2. Login-route (GET: formulier, POST: verifiëren)
# -------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        # Toon het loginscherm
        return render_template("login.html")

    # POST: formulier verwerken
    user_id = request.form.get("user_id", "").strip()

    if not user_id:
        flash("Gebruikers-ID is verplicht.", "error")
        return render_template("login.html")

    try:
        # 1) Check of deze user-id in de 'profiles'-tabel staat
        response = (
            supabase
            .table("profiles")
            .select("*")
            .eq("id", user_id)
            .execute()
        )

        rows = response.data or []

        if len(rows) == 1:
            profile = rows[0]

            # 2) "Inloggen": info in de session bewaren
            session["user_id"] = profile["id"]
            session["full_name"] = profile.get("full_name", "")

            flash("Je bent succesvol ingelogd.", "success")
            return redirect(url_for("dashboard"))
        else:
            # Geen match → generieke foutboodschap
            flash("Verkeerde gebruikersnaam of wachtwoord.", "error")
            return render_template("login.html", user_id=user_id)

    except Exception as e:
        print("Fout bij login:", str(e))
        flash("Er ging iets mis bij het inloggen. Probeer later opnieuw.", "error")
        return render_template("login.html", user_id=user_id)


# -------------------------------------------------
# 3. Simpele dashboard-pagina (alleen voor ingelogde gebruikers)
# -------------------------------------------------

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Je moet ingelogd zijn om het dashboard te bekijken.", "error")
        return redirect(url_for("login"))

    full_name = session.get("full_name", "Onbekende gebruiker")
    return render_template("dashboard.html", full_name=full_name)


# -------------------------------------------------
# 4. Uitloggen
# -------------------------------------------------

@app.route("/logout")
def logout():
    session.clear()
    flash("Je bent uitgelogd.", "success")
    return redirect(url_for("login"))


# -------------------------------------------------
# 5. (Optioneel) root → redirect naar login
# -------------------------------------------------

@app.route("/")
def index():
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)