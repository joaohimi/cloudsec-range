from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.v1.auth_dependencies import AuthContext, get_current_auth_context, require_csrf
from app.api.v1.auth_schemas import AuthResponse, CurrentUserResponse, LoginRequest, MessageResponse, SessionList, SessionRead, UserRead
from app.core.config import settings
from app.core.rate_limit import check_login_rate_limit, clear_login_rate_limit
from app.core.security import digest_token, generate_csrf_token, generate_session_token, verify_against_dummy, verify_password
from app.db.session import get_db
from app.models.auth import AuditEvent, AuthSession, Role, User

router = APIRouter()


def _user_read(user: User) -> UserRead:
    permissions = sorted({permission.code for role in user.roles for permission in role.permissions})
    return UserRead(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        roles=sorted(role.code for role in user.roles),
        permissions=permissions,
    )


def _set_session_cookie(response: Response, token: str, expires_at: datetime) -> None:
    max_age = max(0, int((expires_at - datetime.now(timezone.utc)).total_seconds()))
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=max_age,
        expires=expires_at,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )


def _set_csrf_cookie(response: Response, token: str, expires_at: datetime) -> None:
    max_age = max(0, int((expires_at - datetime.now(timezone.utc)).total_seconds()))
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=token,
        max_age=max_age,
        expires=expires_at,
        httponly=False,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    for cookie_name, http_only in (
        (settings.session_cookie_name, True),
        (settings.csrf_cookie_name, False),
    ):
        response.delete_cookie(
            key=cookie_name,
            httponly=http_only,
            secure=settings.session_cookie_secure,
            samesite="lax",
            path="/",
        )


def _audit(
    db: Session,
    request: Request,
    action: str,
    user_id: UUID | None,
    target_type: str | None = None,
    target_id: str | None = None,
    details: dict | None = None,
    outcome: str = "success",
) -> None:
    db.add(AuditEvent(
        actor_user_id=user_id,
        action=action,
        outcome=outcome,
        target_type=target_type,
        target_id=target_id,
        source_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")[:500] or None,
        details=details or {},
    ))


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    origin = request.headers.get("origin")
    if origin and origin.rstrip("/") not in {item.rstrip("/") for item in settings.cors_origins}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Origem não autorizada.")
    email = payload.email.strip().lower()
    rate_keys = check_login_rate_limit(request, email)
    user = db.scalar(
        select(User)
        .options(selectinload(User.roles).selectinload(Role.permissions))
        .where(User.email == email)
    )

    if user is None:
        verify_against_dummy(payload.password)
        _audit(db, request, "auth.login.failed", None, details={"reason": "invalid_credentials"}, outcome="failure")
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou palavra-passe inválidos.")

    if user.status != "active" or not verify_password(payload.password, user.password_hash):
        if user.status != "active":
            verify_against_dummy(payload.password)
        _audit(db, request, "auth.login.failed", user.id, "user", str(user.id), {"reason": "invalid_credentials_or_disabled"}, outcome="failure")
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou palavra-passe inválidos.")

    clear_login_rate_limit(rate_keys)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=settings.session_ttl_hours)
    raw_token = generate_session_token()
    csrf_token = generate_csrf_token()
    auth_session = AuthSession(
        user_id=user.id,
        token_hash=digest_token(raw_token),
        csrf_token_hash=digest_token(csrf_token),
        expires_at=expires_at,
        last_seen_at=now,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")[:500] or None,
    )
    user.last_login_at = now
    db.add(auth_session)
    db.flush()
    _audit(db, request, "auth.login.succeeded", user.id, "session", str(auth_session.id))

    # Keep at most ten active sessions. The new session is protected from being
    # selected for revocation even when several sessions share the same timestamp.
    old_sessions = list(db.scalars(
        select(AuthSession)
        .where(
            AuthSession.user_id == user.id,
            AuthSession.id != auth_session.id,
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > now,
        )
        .order_by(AuthSession.created_at.desc(), AuthSession.id.desc())
    ))
    for old_session in old_sessions[9:]:
        old_session.revoked_at = now

    db.commit()
    _set_session_cookie(response, raw_token, expires_at)
    _set_csrf_cookie(response, csrf_token, expires_at)
    return AuthResponse(user=_user_read(user), csrf_token=csrf_token, expires_at=expires_at)


@router.get("/me", response_model=CurrentUserResponse)
def me(context: AuthContext = Depends(get_current_auth_context)) -> CurrentUserResponse:
    return CurrentUserResponse(user=_user_read(context.user), expires_at=context.session.expires_at)


@router.post("/logout", response_model=MessageResponse)
def logout(
    request: Request,
    response: Response,
    context: AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
) -> MessageResponse:
    context.session.revoked_at = datetime.now(timezone.utc)
    _audit(db, request, "auth.logout", context.user.id, "session", str(context.session.id))
    db.commit()
    _clear_auth_cookies(response)
    return MessageResponse(message="Sessão terminada.")


@router.get("/sessions", response_model=SessionList)
def list_sessions(
    request: Request,
    context: AuthContext = Depends(get_current_auth_context),
    db: Session = Depends(get_db),
) -> SessionList:
    rows = list(db.scalars(
        select(AuthSession)
        .where(AuthSession.user_id == context.user.id)
        .order_by(AuthSession.created_at.desc())
    ))
    return SessionList(items=[
        SessionRead(
            id=row.id,
            created_at=row.created_at,
            expires_at=row.expires_at,
            last_seen_at=row.last_seen_at,
            revoked_at=row.revoked_at,
            ip_address=row.ip_address,
            user_agent=row.user_agent,
            is_current=row.id == context.session.id,
        ) for row in rows
    ])


@router.delete("/sessions/{session_id}", response_model=MessageResponse)
def revoke_session(
    session_id: UUID,
    request: Request,
    response: Response,
    context: AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
) -> MessageResponse:
    session = db.scalar(select(AuthSession).where(
        AuthSession.id == session_id,
        AuthSession.user_id == context.user.id,
    ))
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sessão não encontrada.")
    if session.revoked_at is None:
        session.revoked_at = datetime.now(timezone.utc)
        _audit(db, request, "auth.session.revoked", context.user.id, "session", str(session.id))
        db.commit()
    if session.id == context.session.id:
        _clear_auth_cookies(response)
    return MessageResponse(message="Sessão revogada.")
