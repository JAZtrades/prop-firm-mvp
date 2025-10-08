"""Authentication endpoints.

Provides registration and login for traders and admins.  The register endpoint
creates a new user and an associated demo account with a starting
balance.  The login endpoint verifies credentials and returns a JWT access
token.
"""
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core.security import create_access_token, get_password_hash, verify_password
from ..db import models
from ..db.session import get_db
from ..core.config import get_settings

from pydantic import BaseModel, EmailStr

router = APIRouter()


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = get_password_hash(user_in.password)
    user = models.User(email=user_in.email, password_hash=hashed)
    db.add(user)
    db.flush()  # ensures user.id is populated

    # Create a default account
    account = models.Account(
        user_id=user.id,
        starting_balance=10000,
        current_balance=10000,
        peak_equity=10000,
    )
    db.add(account)
    db.commit()

    access_token = create_access_token({"sub": user.id})
    return Token(access_token=access_token)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


@router.post("/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token({"sub": user.id})
    return Token(access_token=access_token)
