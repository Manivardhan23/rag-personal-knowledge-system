from fastapi import APIRouter
from config import ADMIN_SECRET
from models.schemas import AdminLoginRequest, AdminLoginResponse

router = APIRouter()


# -- Admin Login
@router.post("/admin/login", response_model=AdminLoginResponse)
def admin_login(request: AdminLoginRequest):
    """Verify admin password. Returns success flag - frontend stores role in localStorage."""
    if request.secret == ADMIN_SECRET:
        return AdminLoginResponse(success=True, message="Welcome back, Admin.")
    return AdminLoginResponse(success=False, message="Incorrect password.")
