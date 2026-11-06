import re
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.v1.auth_dependencies import AuthContext, require_csrf, require_permission
from app.api.v1.user_schemas import (
    ManagedUserList, ManagedUserRead, RoleRead, UserCreateRequest,
    UserRolesUpdateRequest, UserUpdateRequest,
)
from app.core.security import hash_password
from app.db.session import get_db
from app.models.auth import AuditEvent, AuthSession, Role, User

router = APIRouter()
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
ASSIGNABLE_ROLES = {"learner", "reviewer"}


def _serialize_user(user: User) -> ManagedUserRead:
    return ManagedUserRead(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        status=user.status,
        roles=sorted(role.code for role in user.roles),
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )


def _audit(db: Session, request: Request, actor_id: UUID, action: str, target: User, details: dict | None = None) -> None:
    db.add(AuditEvent(
        actor_user_id=actor_id,
        action=action,
        target_type="user",
        target_id=str(target.id),
        outcome="success",
        source_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")[:500] or None,
        details=details or {},
    ))


def _load_user(db: Session, user_id: UUID, lock: bool = False) -> User:
    stmt = select(User).options(selectinload(User.roles)).where(User.id == user_id)
    if lock:
        stmt = stmt.with_for_update()
    user = db.scalar(stmt)
    if user is None:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado.")
    return user


@router.get("/roles", response_model=list[RoleRead])
def list_assignable_roles(
    context: AuthContext = Depends(require_permission("users:manage")),
    db: Session = Depends(get_db),
) -> list[RoleRead]:
    rows = db.scalars(select(Role).where(Role.code.in_(sorted(ASSIGNABLE_ROLES))).order_by(Role.name))
    return [RoleRead(code=row.code, name=row.name, description=row.description) for row in rows]


@router.get("", response_model=ManagedUserList)
def list_users(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None, min_length=1, max_length=160),
    context: AuthContext = Depends(require_permission("users:manage")),
    db: Session = Depends(get_db),
) -> ManagedUserList:
    stmt = select(User).options(selectinload(User.roles))
    count_stmt = select(func.count(User.id))
    if search:
        term = f"%{search.strip()}%"
        predicate = User.email.ilike(term) | User.display_name.ilike(term)
        stmt = stmt.where(predicate)
        count_stmt = count_stmt.where(predicate)
    total = int(db.scalar(count_stmt) or 0)
    rows = list(db.scalars(stmt.order_by(User.created_at.desc()).limit(limit).offset(offset)))
    return ManagedUserList(items=[_serialize_user(row) for row in rows], total=total, limit=limit, offset=offset)


@router.post("", response_model=ManagedUserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreateRequest,
    request: Request,
    context: AuthContext = Depends(require_csrf),
    _permission: AuthContext = Depends(require_permission("users:manage")),
    db: Session = Depends(get_db),
) -> ManagedUserRead:
    email = payload.email.strip().lower()
    display_name = payload.display_name.strip()
    role_codes = sorted(set(payload.role_codes))
    if not EMAIL_RE.fullmatch(email):
        raise HTTPException(status_code=422, detail="Endereço de email inválido.")
    if not display_name:
        raise HTTPException(status_code=422, detail="O nome de apresentação é obrigatório.")
    if len(payload.password.encode("utf-8")) > 512:
        raise HTTPException(status_code=422, detail="A palavra-passe excede o limite de bytes permitido.")
    if not role_codes or not set(role_codes).issubset(ASSIGNABLE_ROLES):
        raise HTTPException(status_code=422, detail="Só é possível atribuir as funções Learner e Reviewer. Owner é atribuído por bootstrap controlado.")
    if db.scalar(select(User.id).where(func.lower(User.email) == email)):
        raise HTTPException(status_code=409, detail="Já existe uma conta com esse email.")
    roles = list(db.scalars(select(Role).where(Role.code.in_(role_codes))))
    if len(roles) != len(role_codes):
        raise HTTPException(status_code=422, detail="Uma ou mais funções não existem.")
    user = User(
        email=email,
        display_name=display_name,
        password_hash=hash_password(payload.password),
        status="active",
        password_changed_at=datetime.now(timezone.utc),
    )
    user.roles = roles
    db.add(user)
    db.flush()
    _audit(db, request, context.user.id, "users.created", user, {"roles": role_codes})
    db.commit()
    db.refresh(user)
    return _serialize_user(user)


@router.patch("/{user_id}", response_model=ManagedUserRead)
def update_user(
    user_id: UUID,
    payload: UserUpdateRequest,
    request: Request,
    context: AuthContext = Depends(require_csrf),
    _permission: AuthContext = Depends(require_permission("users:manage")),
    db: Session = Depends(get_db),
) -> ManagedUserRead:
    if not payload.model_fields_set:
        raise HTTPException(status_code=422, detail="Indica pelo menos um campo para atualizar.")
    user = _load_user(db, user_id, lock=True)
    if payload.display_name is not None:
        display_name = payload.display_name.strip()
        if not display_name:
            raise HTTPException(status_code=422, detail="O nome de apresentação é obrigatório.")
        user.display_name = display_name
    if payload.status is not None and payload.status != user.status:
        if any(role.code == "owner" for role in user.roles):
            raise HTTPException(status_code=409, detail="Contas Owner não podem ser desativadas por esta operação.")
        if payload.status == "disabled":
            now = datetime.now(timezone.utc)
            db.query(AuthSession).filter(
                AuthSession.user_id == user.id,
                AuthSession.revoked_at.is_(None),
            ).update({AuthSession.revoked_at: now}, synchronize_session=False)
        user.status = payload.status
    _audit(db, request, context.user.id, "users.updated", user, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(user)
    return _serialize_user(user)


@router.put("/{user_id}/roles", response_model=ManagedUserRead)
def replace_user_roles(
    user_id: UUID,
    payload: UserRolesUpdateRequest,
    request: Request,
    context: AuthContext = Depends(require_csrf),
    _permission: AuthContext = Depends(require_permission("users:manage")),
    db: Session = Depends(get_db),
) -> ManagedUserRead:
    role_codes = sorted(set(payload.role_codes))
    if not role_codes or not set(role_codes).issubset(ASSIGNABLE_ROLES):
        raise HTTPException(status_code=422, detail="Só é possível atribuir Learner e Reviewer. A função Owner não pode ser atribuída aqui.")
    user = _load_user(db, user_id, lock=True)
    if any(role.code == "owner" for role in user.roles):
        raise HTTPException(status_code=409, detail="As funções da conta Owner não podem ser alteradas por esta operação.")
    roles = list(db.scalars(select(Role).where(Role.code.in_(role_codes))))
    if len(roles) != len(role_codes):
        raise HTTPException(status_code=422, detail="Uma ou mais funções não existem.")
    user.roles = roles
    _audit(db, request, context.user.id, "users.roles_replaced", user, {"roles": role_codes})
    db.commit()
    db.refresh(user)
    return _serialize_user(user)


@router.post("/{user_id}/revoke-sessions")
def revoke_user_sessions(
    user_id: UUID,
    request: Request,
    context: AuthContext = Depends(require_csrf),
    _permission: AuthContext = Depends(require_permission("users:manage")),
    db: Session = Depends(get_db),
) -> dict[str, int]:
    user = _load_user(db, user_id, lock=True)
    now = datetime.now(timezone.utc)
    result = db.query(AuthSession).filter(
        AuthSession.user_id == user.id,
        AuthSession.revoked_at.is_(None),
    ).update({AuthSession.revoked_at: now}, synchronize_session=False)
    _audit(db, request, context.user.id, "users.sessions_revoked", user, {"sessions_revoked": int(result)})
    db.commit()
    return {"sessions_revoked": int(result)}
