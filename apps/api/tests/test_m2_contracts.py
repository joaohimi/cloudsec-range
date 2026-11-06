from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.main import app
from app.db.base import Base
from app.models import LabAttempt, LessonProgress
from app.api.v1.learning_schemas import LessonProgressUpdate, AssessmentAttemptCreate
from app.api.v1.user_schemas import UserCreateRequest


def test_m2_routes_are_registered():
    paths = app.openapi()["paths"]
    expected = {
        ("/api/v1/users", "get"),
        ("/api/v1/users", "post"),
        ("/api/v1/users/{user_id}", "patch"),
        ("/api/v1/users/{user_id}/roles", "put"),
        ("/api/v1/learning/me/progress", "get"),
        ("/api/v1/learning/modules/{module_code}/progress", "get"),
        ("/api/v1/learning/lessons/{lesson_id}/progress", "put"),
        ("/api/v1/learning/labs/{lab_id}/attempts", "post"),
        ("/api/v1/learning/assessments/{assessment_id}/attempts", "post"),
        ("/api/v1/learning/evidence", "post"),
        ("/api/v1/learning/review-queue", "get"),
    }
    actual = {(path, method) for path, methods in paths.items() for method in methods}
    assert expected.issubset(actual)


def test_progress_models_have_user_scoped_identity():
    assert "user_id" in LessonProgress.__table__.columns
    assert "lesson_id" in LessonProgress.__table__.columns
    assert "user_id" in LabAttempt.__table__.columns
    assert "lab_id" in LabAttempt.__table__.columns
    assert "status" in LabAttempt.__table__.columns
    assert any(c.name == "uq_lesson_progress_user_lesson" for c in LessonProgress.__table__.constraints)


def test_lesson_progress_rejects_invalid_status_and_percent():
    valid = LessonProgressUpdate.model_validate({
        "status": "completed", "completion_percent": 100,
        "time_spent_seconds": 300, "last_position": {"section": 4},
    })
    assert valid.status == "completed"
    with pytest.raises(ValidationError):
        LessonProgressUpdate.model_validate({"status": "mastered"})
    with pytest.raises(ValidationError):
        LessonProgressUpdate.model_validate({"status": "in_progress", "completion_percent": 140})


def test_assessment_submission_does_not_accept_score_or_passed():
    submission = AssessmentAttemptCreate.model_validate({"answers": {"Q1": "A minha resposta"}})
    assert submission.answers["Q1"] == "A minha resposta"
    with pytest.raises(ValidationError):
        AssessmentAttemptCreate.model_validate({"answers": {"Q1": "A"}, "score": 100, "passed": True})


def test_user_creation_requires_long_password_and_assignable_role_schema():
    account = UserCreateRequest.model_validate({
        "email": "learner@example.local", "display_name": "Learner Example",
        "password": "Unique-CloudSec-Password-2026", "role_codes": ["learner"],
    })
    assert account.role_codes == ["learner"]
    with pytest.raises(ValidationError):
        UserCreateRequest.model_validate({
            "email": "learner@example.local", "display_name": "Learner Example",
            "password": "short", "role_codes": ["learner"],
        })


def test_alembic_revision_chain_includes_m2():
    migration_path = Path(__file__).parents[1] / "alembic" / "versions" / "0004_learning_progress.py"
    spec = spec_from_file_location("m2_migration", migration_path)
    assert spec and spec.loader
    migration = module_from_spec(spec)
    spec.loader.exec_module(migration)
    assert migration.revision == "0004_learning_progress"
    assert migration.down_revision == "0003_platform_core"
