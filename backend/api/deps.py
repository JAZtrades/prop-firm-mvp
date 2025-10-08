"""Shared dependencies for API routes.

Provides helpers to retrieve the current user and account from the JWT
authorization header.  If no valid token is present, a 401 is returned.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from ..core.security import decode_access_token
from ..db.session import get_db
from ..db import models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    """Decode JWT token and return the corresponding User model."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise credentials_exception
    user_id = payload["sub"]
    user = db.query(models.User).get(user_id)
    if user is None:
        raise credentials_exception
    return user


def get_current_account(
    user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Return the first account associated with the current user."""
    # For simplicity we assume each user has exactly one account
    account = db.query(models.Account).filter(models.Account.user_id == user.id).first()
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return account
