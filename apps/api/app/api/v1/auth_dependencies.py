from dataclasses import dataclass
from datetime import datetime, timezone
import hmac

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import digest_token
from app.db.session import get_db
from app.models.auth import AuthSession, User


@dataclass(frozen=True)
class AuthContext:
    user: User
    session: AuthSession


def get_current_auth_context(
    request: Request,
    db: Session = Depends(get_db),
) -> AuthContext:
    raw_token = request.cookies.get(settings.session_cookie_name)
    if not raw_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Autenticação necessária.")

    session = db.scalar(select(AuthSession).where(AuthSession.token_hash == digest_token(raw_token)))
    now = datetime.now(timezone.utc)
    if session is None or session.revoked_at is not None or session.expires_at <= now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão inválida ou expirada.")

    user = db.scalar(select(User).where(User.id == session.user_id))
    if user is None or user.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Conta indisponível.")

    request.state.auth_context = AuthContext(user=user, session=session)
    return AuthContext(user=user, session=session)


def require_csrf(
    request: Request,
    x_csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
    context: AuthContext = Depends(get_current_auth_context),
) -> AuthContext:
    origin = request.headers.get("origin")
    if origin and origin.rstrip("/") not in {item.rstrip("/") for item in settings.cors_origins}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Origem não autorizada.")
    csrf_cookie = request.cookies.get(settings.csrf_cookie_name)
    if (
        not x_csrf_token
        or not csrf_cookie
        or not hmac.compare_digest(x_csrf_token, csrf_cookie)
        or not hmac.compare_digest(digest_token(x_csrf_token), context.session.csrf_token_hash)
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token CSRF inválido ou ausente.")
    return context


def require_permission(permission_code: str):
    def dependency(context: AuthContext = Depends(get_current_auth_context)) -> AuthContext:
        assigned = {
            permission.code
            for role in context.user.roles
            for permission in role.permissions
        }
        if permission_code not in assigned:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissão insuficiente.")
        return context
    return dependency
