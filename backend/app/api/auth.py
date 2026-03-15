from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user_required
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest, UserResponse
from app.services.auth_service import authenticate_user, build_login_response, get_user_by_email, register_user

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> UserResponse:
    existing_user = get_user_by_email(db, payload.email)
    if existing_user is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")

    user = register_user(
        db=db,
        email=payload.email,
        password=payload.password,
        display_name=payload.display_name,
    )
    return UserResponse.model_validate(user)


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = authenticate_user(db, payload.email, payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return LoginResponse.model_validate(build_login_response(user))


@router.get("/me", response_model=UserResponse)
def auth_me(current_user: User = Depends(get_current_user_required)) -> UserResponse:
    return UserResponse.model_validate(current_user)
