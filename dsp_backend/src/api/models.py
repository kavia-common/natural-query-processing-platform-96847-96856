from typing import Any, Dict, Optional

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    """Request body for user signup."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password (min 6 chars)")


class LoginRequest(BaseModel):
    """Request body for user login."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class TokenResponse(BaseModel):
    """Response model containing access token and token type."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")


class QueryRequest(BaseModel):
    """DSP query request schema; kept minimal for proxy stage."""
    query: str = Field(..., description="Natural language prompt or query for DSP")
    extras: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional extras for DSP processing; forwarded verbatim"
    )


class ProxyErrorResponse(BaseModel):
    """Standardized error structure for proxy failures."""
    error: str = Field(..., description="Short error identifier")
    detail: str = Field(..., description="Detailed description of the error")
    status_code: int = Field(..., description="HTTP status code returned by proxy")
