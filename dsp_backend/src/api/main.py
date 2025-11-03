from typing import Any

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .auth import get_current_user_email
from .config import settings
from .db import create_user, get_db, get_user_by_email, init_db
from .models import LoginRequest, SignupRequest, TokenResponse
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
