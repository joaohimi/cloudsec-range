import json
from pathlib import Path

from app.scripts.seed_linux_m01 import MANIFEST, _load

ROOT = Path(__file__).resolve().parents[3]
CONTENT = ROOT / "content" / "curriculum" / "linux-l1-m01"


def load_manifest():
    return json.loads((CONTENT / "module.json").read_text(encoding="utf-8"))


def test_linux_m01_source_identity_and_duration_are_preserved():
    assert MANIFEST.is_file()
    data = _load()
    assert data["module_code"] == "LINUX-01"
    assert data["source_module_code"] == "M1"
    assert data["module_title"] == "Arquitetura e ecossistema"
    total_minutes = sum(item["minutes"] for item in data["lessons"])
    total_minutes += sum(item["minutes"] for item in data["labs"])
    total_minutes += data["assessment"]["rubric"]["duration_minutes"]
    assert total_minutes == 360


def test_every_lesson_has_a_real_markdown_file_and_competencies():
    data = load_manifest()
    competency_codes = {item["code"] for item in data["competencies"]}
    assert len(data["lessons"]) == 6
    for lesson in data["lessons"]:
        content = (CONTENT / lesson["file"]).read_text(encoding="utf-8")
        assert len(content) > 1200
        assert content.startswith("## Objetivos")
        assert lesson["competency_codes"]
        assert set(lesson["competency_codes"]).issubset(competency_codes)


def test_traceability_references_only_declared_competencies():
    data = load_manifest()
    competency_codes = {item["code"] for item in data["competencies"]}
    assert len(competency_codes) == 6
    for competency in data["competencies"]:
        assert set(competency["prerequisite_codes"]).issubset(competency_codes)
    for lab in data["labs"]:
        assert set(lab["competency_codes"]).issubset(competency_codes)
    for resource in data["resources"]:
        assert resource["url"].startswith("https://")
        assert set(resource["competency_codes"]).issubset(competency_codes)
    assert set(data["ticket"]["competency_codes"]).issubset(competency_codes)
    assert set(data["assessment"]["competency_codes"]).issubset(competency_codes)


def test_labs_are_read_only_or_confined_to_user_home():
    data = load_manifest()
    for lab in data["labs"]:
        safety = lab["manifest"]["safety"]
        assert safety["profile"] == "local-safe"
        assert safety["requires_sudo"] is False
        assert safety["network_access"] is False
        for step in lab["manifest"]["steps"]:
            for command in step.get("commands", []):
                lowered = command.lower()
                assert "sudo " not in lowered
                assert "mkfs" not in lowered
                assert "dd if=" not in lowered
                assert "> /etc/" not in lowered


def test_assessment_threshold_and_critical_errors_exist():
    data = load_manifest()["assessment"]
    rubric = data["rubric"]
    assert data["total_points"] == 100
    assert data["mastery_threshold"] == 80
    assert len(rubric["questions"]) == 12
    assert sum(question["points"] for question in rubric["questions"]) == 100
    assert rubric["critical_errors"]
    assert rubric["mastery_rule"]
