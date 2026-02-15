from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ...core.config import settings
from ...core.database import get_db
from ...core.password_policy import validate_password_strength
from ...core.security import authenticate_user, create_access_token, get_current_active_user
from ...crud.user import create_user, get_user_by_email, get_user_by_username
from ...schemas.user import Token, User, UserCreate
from ..limiter import limiter

router = APIRouter()


@router.post("/token", response_model=Token)
@limiter.limit("5/minute")
async def login_for_access_token(
    request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """Authenticate user and return access token"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user


@router.post("/register", response_model=User)
async def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # 1. Check existing user
    if get_user_by_email(db, email=user_in.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if get_user_by_username(db, username=user_in.username):
        raise HTTPException(status_code=400, detail="Username already taken")

    # 2. Validate Password Strength
    password_check = validate_password_strength(user_in.password, user_inputs=[user_in.username, user_in.email])
    if not password_check["is_strong"]:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Password is too weak",
                "warning": password_check["warning"],
                "suggestions": password_check["suggestions"],
            },
        )

    # 3. Create User
    user = create_user(db, user_in)
    return user


@router.post("/logout")
async def logout_user(current_user: User = Depends(get_current_active_user)):
    """Logout current user"""
    # In stateless JWT, actual logout is client-side (discard token).
    # We could blacklist token here if we implemented a blacklist.
    return {"message": "Logged out successfully"}
