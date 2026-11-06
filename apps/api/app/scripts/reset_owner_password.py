"""Reset the password of an existing active Owner account."""
import argparse
import re
import sys
from datetime import datetime, timezone
from getpass import getpass

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.security import hash_password
from app.db.session import get_session_factory
from app.models.auth import AuditEvent, AuthSession, User

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Redefinir a palavra-passe de uma conta Owner."
    )
    parser.add_argument("--email", required=True)
    args = parser.parse_args()

    email = args.email.strip().lower()

    if not EMAIL_RE.match(email):
        parser.error("Email inválido.")

    password = getpass("Nova palavra-passe (mínimo 15 caracteres): ")
    confirmation = getpass("Confirmar nova palavra-passe: ")

    if password != confirmation:
        print("As palavras-passe não coincidem.", file=sys.stderr)
        return 2

    if (
        len(password) < 15
        or len(password) > 128
        or len(password.encode("utf-8")) > 512
    ):
        print("Palavra-passe fora dos limites permitidos.", file=sys.stderr)
        return 2

    db = get_session_factory()()

    try:
        user = db.scalar(
            select(User)
            .options(selectinload(User.roles))
            .where(User.email == email)
            .with_for_update()
        )

        if user is None:
            print("Conta não encontrada.", file=sys.stderr)
            return 3

        if not any(role.code == "owner" for role in user.roles):
            print("A conta indicada não possui a função Owner.", file=sys.stderr)
            return 4

        if user.status != "active":
            print("A conta não está ativa. Redefinição bloqueada.", file=sys.stderr)
            return 5

        now = datetime.now(timezone.utc)

        user.password_hash = hash_password(password)
        user.password_changed_at = now

        # Revogar todas as sessões anteriores.
        sessions = db.scalars(
            select(AuthSession).where(
                AuthSession.user_id == user.id,
                AuthSession.revoked_at.is_(None),
            )
        )

        for session in sessions:
            session.revoked_at = now

        db.add(AuditEvent(
            actor_user_id=user.id,
            action="auth.owner.password_reset",
            target_type="user",
            target_id=str(user.id),
            outcome="success",
            details={"performed_by": "local_owner_recovery_cli"},
        ))

        db.commit()

        print("Palavra-passe redefinida com sucesso.")
        print("Todas as sessões anteriores foram revogadas.")
        return 0

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
