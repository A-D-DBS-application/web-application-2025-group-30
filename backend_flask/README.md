# Personnel Scheduler - Flask Backend

This is a minimal Flask backend that mirrors the TypeScript backend's API surface for development and testing.

Requirements

- Python 3.10+

Quick start (PowerShell)

```powershell
cd backend_flask
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:SECRET_KEY = "your-secret-here"
python app.py
```

Routes (basic)

- GET `/` - health
- POST `/auth/register` - register {username, password, role}
- POST `/auth/login` - login {username, password} -> returns JWT
- GET `/users/` - list users
- POST `/events/` - create event {title, start, end, assigned_to?}
- GET `/events/` - list events

HTML Frontend

- The Flask app now serves a simple HTML frontend at `/` with vanilla JS.
- Visit `/` for Login/Register (no password required for registration — just provide a username/email).
- Visit `/dashboard` as an employee to submit availability and view assigned events and open shifts to subscribe.
- Visit `/manager` as a manager to create events (name/title, start, end, capacity/amount, type, location, hours), see all events and availabilities, and assign employees to events.

Notes

- This uses an in-memory store (`models.USERS`, `models.EVENTS`). For persistence, connect a DB (MongoDB recommended) and replace model functions.
- JWT verification middleware is not implemented for protected routes; add when integrating frontend-auth.
 - Registration does not require a password: the app uses username-based login and issues JWTs for simple demo flows.
