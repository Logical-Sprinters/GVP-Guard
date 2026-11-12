"""
Authentication & authorization module for GVP-Guard.

Provides:
- Password hashing (SHA-256 with salt)
- JWT-style token creation (signed with HMAC)
- Token verification and session management
- FastAPI dependency functions for role-based access control

Roles:
- viewer: read-only access to incidents, evidence, map
- officer: read + write incidents, decisions, cleanup requests
- admin: read + write + user management, system config

Claim discipline: Authentication is required for all write operations.
Read operations remain available in offline/demo mode.
"""

import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from . import db
from .schemas import ROLES, Token, TokenData, UserIn, UserOut

# In production, load SECRET_KEY from environment variable
SECRET_KEY = Path(__file__).resolve().parent.parent.joinpath(".secret_key").read_text().strip() if Path(__file__).resolve().parent.parent.joinpath(".secret_key").exists() else "gvp-guard-dev-secret-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Hash a password using SHA-256 with a static salt."""
    salt = "gvp-guard-salt-v1"
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def create_access_token(username: str, role: str, expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT-style access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": username,
        "role": role,
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
    }
    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    signature = hmac.new(
        SECRET_KEY.encode("utf-8"), payload_json.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return payload_json + "." + signature


def decode_access_token(token: str) -> TokenData | None:
    """Verify and decode a JWT-style access token. Returns TokenData or None."""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        payload_json, signature = parts
        expected_sig = hmac.new(
            SECRET_KEY.encode("utf-8"), payload_json.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            return None
        payload = json.loads(payload_json)
        exp = payload.get("exp", 0)
        if exp < int(datetime.now(timezone.utc).timestamp()):
            return None
        return TokenData(username=payload.get("sub"), role=payload.get("role"))
    except Exception:
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> TokenData | None:
    """Get current authenticated user from bearer token. Returns None if no token."""
    if credentials is None:
        return None
    token_data = decode_access_token(credentials.credentials)
    if token_data is None:
        return None
    # Verify session still exists in database
    import hashlib as _hashlib
    token_hash = _hashlib.sha256(credentials.credentials.encode("utf-8")).hexdigest()
    session = db.get_session(token_hash)
    if session is None:
        return None
    # Check expiry
    from datetime import datetime as _dt
    if session.get("expires_at") and session["expires_at"] < _dt.now(timezone.utc).isoformat():
        return None
    return token_data


def require_auth(current_user: TokenData | None = Depends(get_current_user)) -> TokenData:
    """Dependency that requires authentication. Raises 401 if not authenticated."""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


def require_role(allowed_roles: list[str]):
    """Dependency factory that requires authentication + specific role."""

    def role_checker(current_user: TokenData = Depends(require_auth)) -> TokenData:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {', '.join(allowed_roles)}",
            )
        return current_user

    return role_checker


def authenticate_user(username: str, password: str) -> UserOut | None:
    """Authenticate user by username/password. Returns UserOut or None."""
    user = db.authenticate_user(username, password)
    if user is None:
        return None
    return UserOut(
        id=user["id"],
        username=user["username"],
        role=user["role"],
        created_at=user.get("created_at"),
    )


def create_user_session(user: UserOut, expires_delta: timedelta | None = None) -> tuple[str, int]:
    """Create an access token and database session for a user. Returns (token, expires_in_seconds)."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
        expires_in = int(expires_delta.total_seconds())
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        expires_in = ACCESS_TOKEN_EXPIRE_MINUTES * 60

    token = create_access_token(user.username, user.role, expires_delta)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    db.create_session(user.id, token_hash, expire.isoformat())
    return token, expires_in


def logout_user(token: str) -> bool:
    """Invalidate a user's session by token."""
    import hashlib as _hashlib
    token_hash = _hashlib.sha256(token.encode("utf-8")).hexdigest()
    return db.delete_session(token_hash)