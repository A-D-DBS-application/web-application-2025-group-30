import os
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
from supabase import create_client, Client

# -------------------------------------------------
# 1. Config & Supabase client
# -------------------------------------------------

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL of SUPABASE_KEY ontbreekt in .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")  # voor flash() etc.


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