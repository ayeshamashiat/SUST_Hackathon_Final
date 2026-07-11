import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from app.auth.models import User, UserRole
from app.auth.security import decode_access_token
from app.db import get_aggregator_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_aggregator_db),
) -> User:
    credentials_error = HTTPException(401, "Could not validate credentials")
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError:
        raise credentials_error

    username = payload.get("sub")
    if not username:
        raise credentials_error

    user = session.exec(select(User).where(User.username == username)).one_or_none()
    if not user:
        raise credentials_error
    return user


def require_roles(*roles: UserRole):
    def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(403, "Not authorized for this action")
        return current_user

    return _check
