from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import LoginRequest, UserOut
from app.security import hash_pin, verify_pin

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=UserOut)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    candidates = db.query(User).filter(User.name == payload.name).all()
    for candidate in candidates:
        if verify_pin(payload.pin, candidate.pin_hash):
            return candidate

    # No existing account with this exact name+pin - create a new one.
    # Duplicate display names are allowed; the (name, pin) pair is the real identity.
    user = User(name=payload.name, pin_hash=hash_pin(payload.pin))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
