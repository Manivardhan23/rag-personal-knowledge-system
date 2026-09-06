import uuid
from fastapi import HTTPException, Header
from typing import Optional

# In-memory session store: token -> username
_sessions: dict[str, str] = {}

def create_session(username: str) -> str:
    token = str(uuid.uuid4())
    _sessions[token] = username
    return token

def validate_session(x_session_token: Optional[str] = Header(None)) -> str:
    """Dependency: validates x-session-token header and returns the collection name."""
    from config import USER_COLLECTION
    if not x_session_token or x_session_token not in _sessions:
        raise HTTPException(status_code=401, detail="Invalid or missing session token. Please log in.")
    return USER_COLLECTION
