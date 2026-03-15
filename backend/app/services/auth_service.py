from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email.lower()).one_or_none()


def get_user_by_id(db: Session, user_id: str) -> User | None:
    return db.get(User, user_id)


def register_user(db: Session, email: str, password: str, display_name: str | None = None) -> User:
    user = User(
        email=email.lower(),
        password_hash=hash_password(password),
        display_name=display_name,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if user is None or not verify_password(password, user.password_hash) or not user.is_active:
        return None
    return user


def build_login_response(user: User) -> dict[str, object]:
    return {
        "access_token": create_access_token(user.id),
        "token_type": "bearer",
        "user": user,
    }
