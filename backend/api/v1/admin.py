from fastapi import APIRouter, HTTPException
from config import APP_USERNAME, APP_PASSWORD
from api.deps import create_session
from models.schemas import LoginRequest, LoginResponse

router = APIRouter()


# ── Login ──────────────────────────────────────────────────
@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    """Validate username + password, return a session token."""
    if request.username == APP_USERNAME and request.password == APP_PASSWORD:
        token = create_session(request.username)
        return LoginResponse(success=True, message=f"Welcome back, {APP_USERNAME}.", token=token)
    raise HTTPException(status_code=401, detail="Incorrect username or password.")
