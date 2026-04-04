"""
User authentication and credential management.

Provides password hashing (bcrypt), user CRUD, and JWT token handling.
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict

import bcrypt as _bcrypt

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """Hash a password with bcrypt."""
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its bcrypt hash."""
    return _bcrypt.checkpw(password.encode(), password_hash.encode())


# ---------------------------------------------------------------------------
# User CRUD
# ---------------------------------------------------------------------------

def _get_pool():
    from utils.db import get_pool
    return get_pool()


def create_user(
    email: str,
    password: Optional[str] = None,
    google_id: Optional[str] = None,
    display_name: Optional[str] = None,
    role: str = "manager",
) -> Optional[Dict]:
    """Create a new user. Returns user dict or None if email already exists."""
    from sqlalchemy import text

    pw_hash = hash_password(password) if password else None
    pool = _get_pool()
    with pool.get_session() as session:
        result = session.execute(
            text("""
                INSERT INTO ahcam.users
                    (email, password_hash, google_id, display_name, role)
                VALUES
                    (:email, :pw_hash, :google_id, :display_name, :role)
                ON CONFLICT (email) DO NOTHING
                RETURNING user_id, email, display_name, role, created_at
            """),
            {
                "email": email.lower().strip(),
                "pw_hash": pw_hash,
                "google_id": google_id,
                "display_name": display_name or email.split("@")[0],
                "role": role,
            },
        )
        row = result.fetchone()
        if not row:
            return None
        return _row_to_user(row, result.keys())


def get_user_by_email(email: str) -> Optional[Dict]:
    """Fetch a user by email address."""
    from sqlalchemy import text
    pool = _get_pool()
    with pool.get_session() as session:
        result = session.execute(
            text("""
                SELECT user_id, email, password_hash, display_name, role, created_at
                FROM ahcam.users
                WHERE email = :email
            """),
            {"email": email.lower().strip()},
        )
        row = result.fetchone()
        if not row:
            return None
        return _row_to_user(row, result.keys())


def get_user_by_id(user_id: str) -> Optional[Dict]:
    """Fetch a user by user_id (UUID)."""
    from sqlalchemy import text
    pool = _get_pool()
    with pool.get_session() as session:
        result = session.execute(
            text("""
                SELECT user_id, email, password_hash, display_name, role, created_at
                FROM ahcam.users
                WHERE user_id = :user_id
            """),
            {"user_id": user_id},
        )
        row = result.fetchone()
        if not row:
            return None
        return _row_to_user(row, result.keys())


def authenticate(email: str, password: str) -> Optional[Dict]:
    """Authenticate by email + password. Returns user dict on success, None on failure."""
    user = get_user_by_email(email)
    if not user:
        return None
    pw_hash = user.get("password_hash")
    if not pw_hash:
        return None
    if not verify_password(password, pw_hash):
        return None
    user.pop("password_hash", None)
    return user


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def create_jwt_token(user_id: str, email: str) -> str:
    """Create a JWT token for session authentication."""
    import jwt

    secret = os.getenv("JWT_SECRET")
    if not secret:
        raise RuntimeError("JWT_SECRET not set in .env")
    payload = {
        "user_id": str(user_id),
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_jwt_token(token: str) -> Optional[Dict]:
    """Decode and verify a JWT token. Returns payload dict or None."""
    import jwt

    secret = os.getenv("JWT_SECRET")
    if not secret:
        return None
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        logger.debug("JWT expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.debug(f"Invalid JWT: {e}")
        return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_reset_token(email: str) -> Optional[str]:
    """Create a short-lived JWT token for password reset (1 hour expiry)."""
    import jwt

    user = get_user_by_email(email)
    if not user:
        return None
    secret = os.getenv("JWT_SECRET")
    if not secret:
        return None
    payload = {
        "user_id": user["user_id"],
        "email": user["email"],
        "purpose": "password_reset",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def verify_reset_token(token: str) -> Optional[Dict]:
    """Verify a password reset token. Returns payload or None."""
    import jwt

    secret = os.getenv("JWT_SECRET")
    if not secret:
        return None
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        if payload.get("purpose") != "password_reset":
            return None
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def update_password(user_id: str, new_password: str) -> bool:
    """Update a user's password."""
    from sqlalchemy import text
    pool = _get_pool()
    pw_hash = hash_password(new_password)
    with pool.get_session() as session:
        result = session.execute(
            text("""
                UPDATE ahcam.users SET password_hash = :pw, updated_at = NOW()
                WHERE user_id = :uid
            """),
            {"pw": pw_hash, "uid": user_id},
        )
        return result.rowcount > 0


def send_reset_email(email: str, reset_url: str) -> bool:
    """Send a password reset email via Postmark."""
    api_key = os.getenv("POSTMARK_API_KEY")
    from_email = os.getenv("FROM_EMAIL", "info@finespresso.org")
    if not api_key:
        logger.error("POSTMARK_API_KEY not set")
        return False
    try:
        from postmarker.core import PostmarkClient
        client = PostmarkClient(server_token=api_key)
        client.emails.send(
            From=from_email,
            To=email,
            Subject="AHCAM - Password Reset",
            HtmlBody=f"""
            <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:480px;margin:0 auto;padding:2rem;">
                <div style="background:linear-gradient(135deg,#0066cc,#004d99);padding:1.5rem;border-radius:12px 12px 0 0;text-align:center;">
                    <h1 style="color:#fff;margin:0;font-size:1.25rem;">Ashland Hill</h1>
                    <p style="color:#cce0ff;margin:0.25rem 0 0;font-size:0.8rem;">Collection Account Management</p>
                </div>
                <div style="background:#fff;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 12px 12px;padding:2rem;">
                    <h2 style="color:#1e293b;font-size:1.1rem;margin:0 0 1rem;">Reset Your Password</h2>
                    <p style="color:#475569;font-size:0.9rem;line-height:1.6;">
                        Click the button below to reset your password. This link expires in 1 hour.
                    </p>
                    <a href="{reset_url}" style="display:inline-block;background:#0066cc;color:#fff;padding:0.75rem 1.5rem;border-radius:8px;text-decoration:none;font-weight:600;font-size:0.9rem;margin:1rem 0;">
                        Reset Password
                    </a>
                    <p style="color:#94a3b8;font-size:0.75rem;margin-top:1.5rem;">
                        If you didn't request this, you can safely ignore this email.
                    </p>
                </div>
            </div>
            """,
            TextBody=f"Reset your AHCAM password: {reset_url}\n\nThis link expires in 1 hour.",
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send reset email: {e}")
        return False


def get_user_by_google_id(google_id: str) -> Optional[Dict]:
    """Fetch a user by Google OAuth ID."""
    from sqlalchemy import text
    pool = _get_pool()
    with pool.get_session() as session:
        result = session.execute(
            text("""
                SELECT user_id, email, password_hash, display_name, role, created_at
                FROM ahcam.users WHERE google_id = :google_id
            """),
            {"google_id": google_id},
        )
        row = result.fetchone()
        if not row:
            return None
        return _row_to_user(row, result.keys())


def link_google_id(email: str, google_id: str) -> bool:
    """Link a Google ID to an existing user."""
    from sqlalchemy import text
    pool = _get_pool()
    with pool.get_session() as session:
        result = session.execute(
            text("""
                UPDATE ahcam.users
                SET google_id = :google_id, updated_at = NOW()
                WHERE email = :email AND google_id IS NULL
            """),
            {"google_id": google_id, "email": email.lower().strip()},
        )
        return result.rowcount > 0


def update_display_name(user_id: str, display_name: str) -> bool:
    """Update a user's display name."""
    from sqlalchemy import text
    pool = _get_pool()
    with pool.get_session() as session:
        result = session.execute(
            text("""
                UPDATE ahcam.users SET display_name = :name, updated_at = NOW()
                WHERE user_id = :uid
            """),
            {"name": display_name, "uid": user_id},
        )
        return result.rowcount > 0


def _row_to_user(row, keys) -> Dict:
    """Convert a DB row to a user dict."""
    d = dict(zip(keys, row))
    if d.get("user_id"):
        d["user_id"] = str(d["user_id"])
    return d
