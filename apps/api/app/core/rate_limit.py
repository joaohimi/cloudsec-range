import hashlib

from fastapi import HTTPException, Request, status

from app.core.config import settings


LOGIN_ATTEMPT_LIMIT = 6
LOGIN_WINDOW_SECONDS = 900


def _opaque_key(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def check_login_rate_limit(request: Request, email: str) -> tuple[str, str]:
    client_ip = request.client.host if request.client else "unknown"
    email_ip_key = f"auth:login:email-ip:{_opaque_key(email.lower() + '|' + client_ip)}"
    ip_key = f"auth:login:ip:{_opaque_key(client_ip)}"
    import redis
    from redis.exceptions import RedisError

    client = redis.Redis.from_url(settings.redis_url, socket_connect_timeout=2, socket_timeout=2)
    try:
        pipe = client.pipeline(transaction=True)
        pipe.incr(email_ip_key)
        pipe.expire(email_ip_key, LOGIN_WINDOW_SECONDS)
        pipe.incr(ip_key)
        pipe.expire(ip_key, LOGIN_WINDOW_SECONDS)
        results = pipe.execute()
    except RedisError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço de autenticação temporariamente indisponível.",
            headers={"Retry-After": "30"},
        ) from exc
    finally:
        client.close()

    email_ip_count, _, ip_count, _ = results
    if email_ip_count > LOGIN_ATTEMPT_LIMIT or ip_count > LOGIN_ATTEMPT_LIMIT * 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiadas tentativas. Aguarda antes de tentar novamente.",
            headers={"Retry-After": str(LOGIN_WINDOW_SECONDS)},
        )
    return email_ip_key, ip_key


def clear_login_rate_limit(keys: tuple[str, str]) -> None:
    try:
        import redis
        from redis.exceptions import RedisError
    except ImportError:
        return
    client = redis.Redis.from_url(settings.redis_url, socket_connect_timeout=2, socket_timeout=2)
    try:
        client.delete(*keys)
    except RedisError:
        # A successful login must not be turned into a failure because counters
        # could not be cleared. Their TTL still limits their lifetime.
        pass
    finally:
        client.close()
