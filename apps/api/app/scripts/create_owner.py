"""Create the initial platform owner interactively.

Usage (inside the API container):
    python -m app.scripts.create_owner --email owner@example.local --name "Platform Owner"

The password is requested interactively and is never accepted as a command-line
argument or written to application logs.
"""
import argparse
from getpass import getpass
import re
import sys
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import get_session_factory
from app.models.auth import AuditEvent, Role, User


EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def main() -> int:
    parser = argparse.ArgumentParser(description="Criar a primeira conta Owner da CloudSec Range.")
    parser.add_argument("--email", required=True, help="Email da conta administrativa.")
    parser.add_argument("--name", required=True, help="Nome de apresentação.")
    args = parser.parse_args()

    email = args.email.strip().lower()
    display_name = args.name.strip()
    if not EMAIL_RE.match(email):
        parser.error("Email inválido.")
    if not 2 <= len(display_name) <= 160:
        parser.error("O nome deve ter entre 2 e 160 caracteres.")

    password = getpass("Palavra-passe do Owner (mínimo 15 caracteres): ")
    confirmation = getpass("Confirmar palavra-passe: ")
    if password != confirmation:
        print("As palavras-passe não coincidem.", file=sys.stderr)
        return 2
    if len(password) < 15 or len(password) > 128 or len(password.encode("utf-8")) > 512:
        print("A palavra-passe deve ter pelo menos 15 caracteres e no máximo 128 bytes.", file=sys.stderr)
        return 2

    session = get_session_factory()()
    try:
        owner_role = session.scalar(select(Role).where(Role.code == "owner"))
        if owner_role is None:
            print("As roles ainda não existem. Confirma se a migração 0003 foi aplicada.", file=sys.stderr)
            return 3
        existing_owner = session.scalar(
            select(User.id)
            .join(User.roles)
            .where(Role.code == "owner")
            .limit(1)
        )
        if existing_owner:
            print("Já existe uma conta Owner. A criação inicial foi bloqueada.", file=sys.stderr)
            return 4
        if session.scalar(select(User.id).where(User.email == email)):
            print("Já existe uma conta com esse email.", file=sys.stderr)
            return 5

        user = User(
            email=email,
            display_name=display_name,
            password_hash=hash_password(password),
            status="active",
            password_changed_at=datetime.now(timezone.utc),
        )
        user.roles.append(owner_role)
        session.add(user)
        session.flush()
        session.add(AuditEvent(
            actor_user_id=user.id,
            action="auth.owner.bootstrap_created",
            target_type="user",
            target_id=str(user.id),
            outcome="success",
            details={"created_by": "interactive_bootstrap_cli"},
        ))
        session.commit()
        print(f"Conta Owner criada: {email}")
        print("Por segurança, guarda a palavra-passe num gestor de palavras-passe.")
        return 0
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
