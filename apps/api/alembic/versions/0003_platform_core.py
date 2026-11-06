"""Platform Core: users, RBAC, server-side sessions and audit events.

Revision ID: 0003_platform_core
Revises: 0002_curriculum_engine
Create Date: 2026-11-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0003_platform_core"
down_revision: Union[str, None] = "0002_curriculum_engine"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = sa.Uuid()
JSONB = postgresql.JSONB(astext_type=sa.Text())
NOW = sa.func.now()


def timestamps():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=NOW),
    ]


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("display_name", sa.String(160), nullable=False),
        sa.Column("password_hash", sa.String(512), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column("password_changed_at", sa.DateTime(timezone=True)),
        *timestamps(),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.CheckConstraint("status IN ('active', 'disabled', 'pending')", name="ck_users_status"),
    )
    op.create_index("ix_users_status", "users", ["status"])

    op.create_table(
        "roles",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("code", sa.String(60), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.true()),
        *timestamps(),
        sa.UniqueConstraint("code", name="uq_roles_code"),
    )

    op.create_table(
        "permissions",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.Text()),
        *timestamps(),
        sa.UniqueConstraint("code", name="uq_permissions_code"),
    )

    op.create_table(
        "user_roles",
        sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", UUID, sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_table(
        "role_permissions",
        sa.Column("role_id", UUID, sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("permission_id", UUID, sa.ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "auth_sessions",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("csrf_token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("ip_address", sa.String(64)),
        sa.Column("user_agent", sa.String(500)),
        *timestamps(),
        sa.UniqueConstraint("token_hash", name="uq_auth_sessions_token_hash"),
    )
    op.create_index("ix_auth_sessions_user_expires", "auth_sessions", ["user_id", "expires_at"])

    op.create_table(
        "audit_events",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("actor_user_id", UUID, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(120), nullable=False),
        sa.Column("target_type", sa.String(80)),
        sa.Column("target_id", sa.String(120)),
        sa.Column("outcome", sa.String(30), nullable=False, server_default="success"),
        sa.Column("source_ip", sa.String(64)),
        sa.Column("user_agent", sa.String(500)),
        sa.Column("details", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        *timestamps(),
    )
    op.create_index("ix_audit_events_created_at", "audit_events", ["created_at"])
    op.create_index("ix_audit_events_actor_created", "audit_events", ["actor_user_id", "created_at"])
    op.create_index("ix_audit_events_action", "audit_events", ["action"])

    op.execute(sa.text(
        "INSERT INTO roles (id, code, name, description, is_system) VALUES "
        "(gen_random_uuid(), 'owner', 'Owner', 'Administração integral da plataforma.', true), "
        "(gen_random_uuid(), 'learner', 'Learner', 'Aprendizagem, laboratórios, submissões e portfólio próprio.', true), "
        "(gen_random_uuid(), 'reviewer', 'Reviewer', 'Revisão técnica de tickets, avaliações e evidências.', true)"
    ))

    permission_data = [
        ("platform:admin", "Administrar plataforma", "Acesso administrativo global."),
        ("users:manage", "Gerir utilizadores", "Criar, desativar e atribuir funções a utilizadores."),
        ("audit:read", "Consultar auditoria", "Consultar eventos de auditoria."),
        ("learning:read", "Consultar aprendizagem", "Aceder ao conteúdo do Learning Center."),
        ("learning:progress", "Registar progresso", "Registar progresso e domínio de competências."),
        ("labs:execute", "Executar laboratórios", "Executar laboratórios autorizados."),
        ("tickets:read", "Consultar tickets", "Consultar tickets do Internship Center."),
        ("tickets:submit", "Submeter tickets", "Criar e submeter trabalho profissional simulado."),
        ("tickets:review", "Rever tickets", "Rever e classificar tickets submetidos."),
        ("assessments:attempt", "Realizar avaliações", "Submeter tentativas de avaliação."),
        ("assessments:review", "Rever avaliações", "Corrigir e validar avaliações."),
        ("portfolio:read", "Consultar portfólio", "Consultar evidências e portfólio autorizado."),
        ("portfolio:manage", "Gerir portfólio", "Gerir evidências próprias."),
        ("portfolio:review", "Rever portfólio", "Rever evidências de outros utilizadores."),
        ("sessions:manage", "Gerir sessões", "Consultar e revogar sessões próprias."),
    ]
    for code, name, description in permission_data:
        op.execute(sa.text(
            "INSERT INTO permissions (id, code, name, description) "
            "VALUES (gen_random_uuid(), :code, :name, :description)"
        ).bindparams(code=code, name=name, description=description))

    owner_codes = {code for code, _, _ in permission_data}
    learner_codes = {
        "learning:read", "learning:progress", "labs:execute", "tickets:read", "tickets:submit",
        "assessments:attempt", "portfolio:read", "portfolio:manage", "sessions:manage",
    }
    reviewer_codes = {
        "learning:read", "labs:execute", "tickets:read", "tickets:review", "assessments:review",
        "portfolio:read", "portfolio:review", "sessions:manage",
    }
    # Use explicit INSERT..SELECT statements; SQLAlchemy bulk_insert cannot bind
    # SQL expressions consistently across dialects.
    for role_code, codes in (("owner", owner_codes), ("learner", learner_codes), ("reviewer", reviewer_codes)):
        for permission_code in sorted(codes):
            op.execute(sa.text(
                "INSERT INTO role_permissions (role_id, permission_id) "
                "SELECT r.id, p.id FROM roles r CROSS JOIN permissions p "
                "WHERE r.code = :role_code AND p.code = :permission_code"
            ).bindparams(role_code=role_code, permission_code=permission_code))


def downgrade() -> None:
    op.drop_index("ix_audit_events_action", table_name="audit_events")
    op.drop_index("ix_audit_events_actor_created", table_name="audit_events")
    op.drop_index("ix_audit_events_created_at", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_auth_sessions_user_expires", table_name="auth_sessions")
    op.drop_table("auth_sessions")
    op.drop_table("role_permissions")
    op.drop_table("user_roles")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_index("ix_users_status", table_name="users")
    op.drop_table("users")
