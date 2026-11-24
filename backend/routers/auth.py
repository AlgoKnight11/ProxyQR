from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
import datetime

from backend.database import get_db
from backend.models import User
from backend.schemas import LoginRequest, TokenResponse, UserOut
from backend.auth import verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
def login(login_req: LoginRequest, response: Response, db: Session = Depends(get_db)):
    identifier = login_req.identifier.strip()
    password = login_req.password

    # Query by roll_no or email (case-insensitive for email)
    user = db.query(User).filter(
        (User.roll_no == identifier) | (User.email == identifier.lower())
    ).first()

    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please check your Roll Number/Email and password.",
        )

    # Generate JWT
    token_data = {
        "sub": str(user.id),
        "role": user.role,
        "name": user.full_name,
        "roll_no": user.roll_no or "",
        "email": user.email or "",
    }
    access_token = create_access_token(token_data)

    # Set HTTP-only cookie for secure browser navigation
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        samesite="lax",
        secure=False, # Set to True in HTTPS production
        max_age=60 * 60 * 24 # 1 day
    )

    return TokenResponse(
        access_token=access_token,
        user=UserOut.model_validate(user)
    )

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserOut)
def get_profile(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)
