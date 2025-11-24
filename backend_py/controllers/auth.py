import os
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import jwt
import bcrypt
from models import create_user, find_user_by_username, UserOut

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
ALGORITHM = "HS256"

class RegisterPayload(BaseModel):
    username: str
    password: str
    role: str = "employee"

class LoginPayload(BaseModel):
    username: str
    password: str

@router.post("/register", response_model=UserOut)
def register(payload: RegisterPayload):
    existing = find_user_by_username(payload.username)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
    hashed = bcrypt.hashpw(payload.password.encode(), bcrypt.gensalt()).decode()
    user = create_user(payload.username, hashed, payload.role)
    return {"id": user["id"], "username": user["username"], "role": user["role"]}

@router.post("/login")
def login(payload: LoginPayload):
    user = find_user_by_username(payload.username)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not bcrypt.checkpw(payload.password.encode(), user["password"].encode()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = jwt.encode({"sub": user["id"]}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}
