from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.deps import get_current_user
from app.core.security import create_access_token, verify_password
from app.models.models import User
from app.schemas.schemas import TokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == form.username)).one_or_none()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(401, "Incorrect username or password")

    return TokenOut(
        access_token=create_access_token(user),
        role=user.role,
        display_name=user.display_name,
        agent_id=user.agent_id,
        provider_id=user.provider_id,
    )


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return UserOut(
        username=current_user.username,
        role=current_user.role,
        display_name=current_user.display_name,
        agent_id=current_user.agent_id,
        provider_id=current_user.provider_id,
    )
