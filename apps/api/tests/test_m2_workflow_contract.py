from pathlib import Path

import pytest
from pydantic import ValidationError

from app.api.v1.learning_schemas import AssessmentAttemptCreate, CompetencyReview
from app.main import app


def test_assessment_submission_does_not_accept_client_supplied_score_or_feedback():
    with pytest.raises(ValidationError):
        AssessmentAttemptCreate.model_validate({"answers": {"q1": "answer"}, "score": 100})
    with pytest.raises(ValidationError):
        AssessmentAttemptCreate.model_validate({"answers": {"q1": "answer"}, "passed": True})


def test_competency_review_targets_an_explicit_learner():
    payload = CompetencyReview.model_validate({
        "learner_user_id": "11111111-1111-4111-8111-111111111111",
        "status": "demonstrated",
        "notes": "Evidência prática revista e validada.",
    })
    assert str(payload.learner_user_id) == "11111111-1111-4111-8111-111111111111"
    with pytest.raises(ValidationError):
        CompetencyReview.model_validate({"status": "demonstrated", "notes": "Sem alvo."})


def test_m2_api_routes_and_retired_legacy_routes_are_explicit():
    paths = app.openapi()["paths"]
    assert "/api/v1/users" in paths
    assert "/api/v1/learning/me/progress" in paths
    assert "/api/v1/learning/review-queue" in paths
    assert "410" in paths["/api/v1/curriculum/assessments/{assessment_id}/attempts"]["post"]["responses"]
    assert "410" in paths["/api/v1/curriculum/evidence"]["post"]["responses"]


def test_curriculum_traceability_is_scoped_to_authenticated_user():
    source = (Path(__file__).resolve().parents[1] / "app" / "api" / "v1" / "curriculum.py").read_text(encoding="utf-8")
    assert "Evidence.user_id == context.user.id" in source
    assert "CompetencyProgress.user_id == context.user.id" in source
    assert 'CompetencyProgress.learner_key == "primary"' not in source


def test_reviewer_endpoints_enforce_separation_of_duties():
    source = (Path(__file__).resolve().parents[1] / "app" / "api" / "v1" / "learning.py").read_text(encoding="utf-8")
    assert "não podes rever a tua própria submissão" in source
    assert "não podes corrigir a tua própria avaliação" in source
    assert "não podes rever a tua própria evidência" in source
    assert "não podes validar a tua própria competência" in source
    assert "LabAttempt.user_id != context.user.id" in source
    assert "AssessmentAttempt.user_id != context.user.id" in source
    assert "Evidence.user_id != context.user.id" in source
