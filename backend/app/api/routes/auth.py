from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserOut
from app.services.auth_service import authenticate_user, issue_token
from app.services.log_service import log_action
from app.models.log import LogAction
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Login de administrador. Rate limit: 5 req/min por IP (via SlowAPIMiddleware)."""
    # O rate limit específico desta rota é gerido pelo decorator aplicado em main.py
    # após o router ser registado. Ver _apply_login_rate_limit() em main.py.
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas.",
        )

    token = issue_token(user)
    ip = request.client.host if request.client else None

    log_action(
        db,
        action=LogAction.login,
        user_id=user.id,
        detail=f"Login via {ip}",
        ip_address=ip,
    )

    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
