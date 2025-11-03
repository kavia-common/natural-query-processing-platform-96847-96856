from typing import Any, Dict, Optional

import httpx
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .auth import get_current_user_email
from .config import settings
from .db import create_user, get_db, get_user_by_email, init_db
from .models import (
    LoginRequest,
    SignupRequest,
    TokenResponse,
    QueryRequest,
    ProxyErrorResponse,
)
from .security import create_access_token, hash_password, verify_password

# Initialize DB schema on startup
init_db()

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    openapi_tags=[
        {"name": "health", "description": "Service health endpoints"},
        {"name": "auth", "description": "Authentication endpoints"},
        {"name": "dsp", "description": "DSP query proxy endpoints"},
    ],
)

# Configure CORS based on env
allow_all = settings.CORS_ALLOW_ORIGINS == ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all else settings.CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["health"], summary="Health Check")
def health_check() -> dict[str, str]:
    """Health check endpoint to verify the service is running."""
    return {"message": "Healthy"}


@app.post(
    "/signup",
    response_model=TokenResponse,
    tags=["auth"],
    summary="Create user account",
    responses={
        201: {"description": "User created"},
        400: {"description": "User already exists"},
    },
    status_code=201,
)
def signup(payload: SignupRequest) -> TokenResponse:
    """Create a new user with email and password and return an access token.

    Parameters:
    - payload: SignupRequest containing email and password

    Returns:
    - TokenResponse: bearer access token
    """
    with get_db() as conn:
        existing = get_user_by_email(conn, payload.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists",
            )
        pw_hash = hash_password(payload.password)
        create_user(conn, payload.email, pw_hash)

    token = create_access_token(subject=payload.email)
    return TokenResponse(access_token=token, token_type="bearer")


@app.post(
    "/login",
    response_model=TokenResponse,
    tags=["auth"],
    summary="User login",
    responses={
        200: {"description": "Authenticated"},
        401: {"description": "Invalid credentials"},
    },
)
def login(payload: LoginRequest) -> TokenResponse:
    """Authenticate a user and return an access token.

    Parameters:
    - payload: LoginRequest with email and password

    Returns:
    - TokenResponse: bearer access token
    """
    with get_db() as conn:
        user = get_user_by_email(conn, payload.email)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        if not verify_password(payload.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

    token = create_access_token(subject=payload.email)
    return TokenResponse(access_token=token, token_type="bearer")


@app.get(
    "/me",
    tags=["auth"],
    summary="Get current user",
    responses={200: {"description": "Current user email"}},
)
def me(current_email: str = Depends(get_current_user_email)) -> dict[str, Any]:
    """Return the current authenticated user's email address."""
    return {"email": current_email}


@app.post(
    "/dsp/query",
    tags=["dsp"],
    summary="Proxy query to internal DSP service",
    response_description="JSON response returned by the DSP service",
    responses={
        200: {"description": "Successful proxy to DSP"},
        400: {"description": "Bad request to DSP", "model": ProxyErrorResponse},
        401: {"description": "Unauthorized"},
        502: {"description": "DSP upstream error", "model": ProxyErrorResponse},
        504: {"description": "DSP timeout", "model": ProxyErrorResponse},
    },
)
async def dsp_query(
    payload: QueryRequest,
    current_email: str = Depends(get_current_user_email),
) -> Dict[str, Any]:
    """Proxy the query to the internal DSP service.

    This endpoint is protected with JWT (Bearer) auth via get_current_user_email.
    It forwards the JSON body {query, extras?} to the internal DSP endpoint:
      POST {DSP_INTERNAL_BASE}/dsp/query

    Security:
    - Uses a strict httpx.BaseURL client with a fixed base URL from environment
      to prevent SSRF and path injection.
    - Only forwards the allowed fields (query, extras).

    Parameters:
    - payload: QueryRequest containing query and optional extras.

    Returns:
    - The proxied JSON response from the DSP service on success.
    - A structured error with clear details on failure.
    """
    # Prepare strict base URL client to avoid SSRF
    base_url = settings.DSP_INTERNAL_BASE.rstrip("/")
    # Only allow the /dsp/query path under the fixed base URL
    timeout = settings.DSP_TIMEOUT_SEC

    # Construct the minimal body to forward
    body: Dict[str, Any] = {"query": payload.query}
    if getattr(payload, "extras", None) is not None:
        body["extras"] = payload.extras  # forwarded verbatim

    try:
        async with httpx.AsyncClient(base_url=base_url, timeout=timeout) as client:
            # Explicit path to avoid user-controlled URL parts
            resp = await client.post("/dsp/query", json=body)
    except httpx.ReadTimeout:
        # 504 Gateway Timeout semantics for upstream timeout
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={
                "error": "upstream_timeout",
                "detail": "Timed out waiting for response from DSP service",
                "status_code": 504,
            },
        )
    except httpx.HTTPError as e:
        # 502 Bad Gateway for generic upstream errors
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "upstream_error",
                "detail": f"Error communicating with DSP service: {str(e)}",
                "status_code": 502,
            },
        )

    # If upstream returns non-2xx, relay a structured error while preserving status
    if resp.status_code < 200 or resp.status_code >= 300:
        # Attempt to parse JSON error; fall back to text
        err_detail: Optional[Any]
        try:
            err_detail = resp.json()
        except Exception:
            err_detail = resp.text
        raise HTTPException(
            status_code=400 if resp.status_code == 400 else status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "upstream_bad_response",
                "detail": {
                    "status": resp.status_code,
                    "body": err_detail,
                },
                "status_code": 400 if resp.status_code == 400 else 502,
            },
        )

    # Return the JSON body from upstream if possible; otherwise return text
    try:
        return resp.json()
    except Exception:
        return {"data": resp.text}
