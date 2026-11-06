import hashlib
import hmac
import secrets
import unicodedata

try:
    from pwdlib import PasswordHash
    _password_hash = PasswordHash.recommended()
except ImportError:  # pragma: no cover - fallback for constrained local test environments
    from argon2 import PasswordHasher

    class _Argon2Compatibility:
        def __init__(self):
            self._hasher = PasswordHasher()

        def hash(self, password: str) -> str:
            return self._hasher.hash(password)

        def verify(self, password: str, encoded_hash: str) -> bool:
            try:
                return self._hasher.verify(encoded_hash, password)
            except Exception:
                return False

    _password_hash = _Argon2Compatibility()

# A fixed dummy Argon2 hash is used for unknown accounts so login responses do not
# reveal account existence through a large timing difference.
_DUMMY_HASH = _password_hash.hash("cloudsec-range-dummy-password-never-used")


def _normalize_password(password: str) -> str:
    return unicodedata.normalize("NFC", password)


def hash_password(password: str) -> str:
    return _password_hash.hash(_normalize_password(password))


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        return _password_hash.verify(_normalize_password(password), encoded_hash)
    except (ValueError, TypeError):
        return False


def verify_against_dummy(password: str) -> None:
    _password_hash.verify(_normalize_password(password), _DUMMY_HASH)


def generate_session_token() -> str:
    """Generate a high-entropy opaque browser session token."""
    return secrets.token_urlsafe(48)


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def digest_token(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def constant_time_digest_match(value: str, stored_digest: str) -> bool:
    return hmac.compare_digest(digest_token(value), stored_digest)
