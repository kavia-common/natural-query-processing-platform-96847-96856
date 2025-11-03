from datetime import datetime, timezone
from typing import Any, Dict, Optional

import jwt  # PyJWT
from passlib.context import CryptContext

from .config import settings

# Password hashing context using bcrypt
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# PUBLIC_INTERFACE
def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return _pwd_context.hash(plain_password)


# PUBLIC_INTERFACE
def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored hash."""
    return _pwd_context.verify(plain_password, password_hash)


# PUBLIC_INTERFACE
def create_access_token(subject: str, extra_claims: Optional[Dict[str, Any]] = None) -> str:
    """Create a signed JWT access token.

    Args:
        subject: The subject claim (e.g., user email or ID).
        extra_claims: Optional extra claims to include in token.

    Returns:
        Encoded JWT as a string.
    """
    now = datetime.now(tz=timezone.utc)
    expire: datetime = now + settings.jwt_exp_delta
    payload: Dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)
    return token


# PUBLIC_INTERFACE
def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT, returning the payload claims.

    Raises jwt.ExpiredSignatureError, jwt.InvalidTokenError on invalid tokens.
    """
    payload = jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALG],
        options={"require": ["exp", "iat", "sub"]},
    )
    return payload
