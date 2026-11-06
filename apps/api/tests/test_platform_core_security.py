from app.core.security import (
    constant_time_digest_match,
    digest_token,
    generate_csrf_token,
    generate_session_token,
    hash_password,
    verify_password,
)


def test_password_hash_verifies_without_storing_plaintext():
    password = "a-strong-example-password-2026"
    encoded = hash_password(password)
    assert encoded != password
    assert encoded.startswith("$argon2id$")
    assert verify_password(password, encoded)
    assert not verify_password("wrong-password", encoded)


def test_session_tokens_are_random_and_only_the_digest_is_stored():
    first = generate_session_token()
    second = generate_session_token()
    assert first != second
    assert len(first) >= 60
    assert digest_token(first) != first
    assert constant_time_digest_match(first, digest_token(first))
    assert not constant_time_digest_match(second, digest_token(first))


def test_csrf_tokens_have_independent_entropy():
    csrf = generate_csrf_token()
    session = generate_session_token()
    assert csrf != session
    assert len(csrf) >= 40


def test_permission_dependency_allows_only_assigned_permission():
    from types import SimpleNamespace
    from fastapi import HTTPException
    import pytest
    from app.api.v1.auth_dependencies import AuthContext, require_permission

    allowed_user = SimpleNamespace(roles=[SimpleNamespace(permissions=[SimpleNamespace(code="learning:read")])])
    context = AuthContext(user=allowed_user, session=SimpleNamespace())
    assert require_permission("learning:read")(context) is context
    with pytest.raises(HTTPException) as exc:
        require_permission("platform:admin")(context)
    assert exc.value.status_code == 403


def test_password_normalization_is_consistent_for_unicode():
    composed = "Café-phrase-with-enough-length-2026"
    decomposed = "Cafe\u0301-phrase-with-enough-length-2026"
    encoded = hash_password(composed)
    assert verify_password(decomposed, encoded)


def test_failed_authentication_audit_events_are_recorded_as_failures():
    from types import SimpleNamespace
    from uuid import uuid4
    from app.api.v1.auth import _audit

    class FakeDB:
        def __init__(self):
            self.items = []

        def add(self, item):
            self.items.append(item)

    db = FakeDB()
    request = SimpleNamespace(
        client=SimpleNamespace(host="127.0.0.1"),
        headers={"user-agent": "platform-core-test"},
    )
    _audit(db, request, "auth.login.failed", uuid4(), "user", "user-1", {"reason": "invalid_credentials"}, outcome="failure")

    assert len(db.items) == 1
    assert db.items[0].outcome == "failure"
    assert db.items[0].action == "auth.login.failed"
