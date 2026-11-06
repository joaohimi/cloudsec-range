from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.api.v1.auth_dependencies import require_permission
from app.db.session import get_db

router = APIRouter()


class SystemInfo(BaseModel):
    name: str
    version: str
    environment: str
    status: str


@router.get("/info", response_model=SystemInfo)
def system_info() -> SystemInfo:
    return SystemInfo(
        name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        status="running",
    )


@router.get("/database-check", dependencies=[Depends(require_permission("platform:admin"))])
def database_check(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"database": "ok"}
