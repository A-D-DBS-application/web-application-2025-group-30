import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from controllers import auth, users, events

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")

app = FastAPI(title="Personnel Scheduler (Python)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"]) 
app.include_router(users.router, prefix="/users", tags=["users"]) 
app.include_router(events.router, prefix="/events", tags=["events"]) 

@app.get("/")
def root():
    return {"message": "Personnel Scheduler Python backend is running"}
