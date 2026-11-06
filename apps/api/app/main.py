from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.session import get_engine

if settings.app_env.lower() not in {"development", "local", "test"} and not settings.session_cookie_secure:
    raise RuntimeError("SESSION_COOKIE_SECURE=true é obrigatório fora do ambiente local HTTP.")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Learning and professional-practice platform for Cloud Security.",
    docs_url="/docs" if settings.app_env == "development" else None,
    redoc_url="/redoc" if settings.app_env == "development" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-CSRF-Token"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health/live", tags=["health"], include_in_schema=False)
def liveness() -> dict[str, str]:
    return {"status": "alive"}


@app.get("/health/ready", tags=["health"], include_in_schema=False)
def readiness() -> dict[str, object]:
    checks: dict[str, str] = {}
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = "unavailable"
        raise HTTPException(status_code=503, detail={"status": "not_ready", "checks": checks}) from exc

    try:
        import redis

        client = redis.Redis.from_url(settings.redis_url, socket_connect_timeout=2, socket_timeout=2)
        client.ping()
        client.close()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = "unavailable"
        raise HTTPException(status_code=503, detail={"status": "not_ready", "checks": checks}) from exc

    return {"status": "ready", "checks": checks}
