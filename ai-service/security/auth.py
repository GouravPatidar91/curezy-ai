from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt  # Direct bcrypt to avoid passlib issues on Render
from fastapi import Depends, HTTPException, Header, Request, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "curezy-super-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

bearer_scheme = HTTPBearer()

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt directly."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False

# ── Pre-hashed passwords
_DOCTOR_HASH = get_password_hash("doctor123")
_ADMIN_HASH  = get_password_hash("admin123")

USERS_DB = {
    "doctor_001": {
        "user_id": "doctor_001",
        "username": "dr_sharma",
        "hashed_password": _DOCTOR_HASH,
        "role": "doctor",
        "hospital_id": "H001"
    },
    "admin_001": {
        "user_id": "admin_001",
        "username": "admin",
        "hashed_password": _ADMIN_HASH,
        "role": "admin",
        "hospital_id": None
    }
}


# ─────────────────────────────────────────
# TOKEN UTILS
# ─────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def authenticate_user(username: str, password: str) -> Optional[dict]:
    for user in USERS_DB.values():
        if user["username"] == username:
            if verify_password(password, user["hashed_password"]):
                return user
    return None


# ─────────────────────────────────────────
# DEPENDENCIES
# ─────────────────────────────────────────

async def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    # ── API Key auth
    if authorization and authorization.startswith("Bearer curezy_live_"):
        api_key = authorization.replace("Bearer ", "")
        from security.api_key_manager import APIKeyManager
        manager = APIKeyManager()
        key_data = await manager.validate_key(api_key)
        if not key_data:
            raise HTTPException(status_code=401, detail="Invalid API key")
        return {"user_id": key_data.get("client"), "role": "api", "type": "apikey"}

    # ── Supabase JWT auth (ECC P-256)
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
        try:
            from supabase import create_client
            supabase = create_client(
                os.getenv("SUPABASE_URL"),
                os.getenv("SUPABASE_KEY")
            )
            # Verify token using Supabase
            user = supabase.auth.get_user(token)
            if not user or not user.user:
                raise HTTPException(status_code=401, detail="Invalid or expired token")
            return {
                "user_id": user.user.id,
                "role": user.user.role or "user",
                "type": "supabase",
                "email": user.user.email
            }
        except Exception as e:
            print(f"[Auth] Supabase token validation failed: {e}")
            raise HTTPException(status_code=401, detail="Invalid or expired token")

    raise HTTPException(status_code=401, detail="Authorization required")


def require_doctor(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user["role"] not in ("doctor", "admin", "api_client"):
        raise HTTPException(status_code=403, detail="Doctor access required")
    return current_user


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user