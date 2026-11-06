import json
from pathlib import Path

from app.main import app
from app.db.base import Base
from app import models  # noqa: F401
from sqlalchemy.orm import configure_mappers


ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / "content" / "curriculum" / "canonical-roadmap-v1.json"


def test_canonical_linux_map_preserves_28_modules_and_nine_blocks():
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    linux = next(track for track in payload["tracks"] if track["code"] == "LINUX")
    modules = [module for block in linux["blocks"] for module in block["modules"]]
    assert len(linux["blocks"]) == 9
    assert len(modules) == 28
    assert sum(module["hours"] for module in modules) == 312
    assert sum(block.get("environment_lab", {}).get("hours", 0) for block in linux["blocks"]) == 6
    assert [block["code"] for block in linux["blocks"]] == [f"L{i}" for i in range(1, 10)]
    assert [module["source_module_code"] for block in linux["blocks"] for module in block["modules"]] == [
        "M1", "M2", "M3", "M4", "M7", "M5", "M6", "M8", "M23", "M9",
        "M10", "M11", "M12", "M13", "M14", "M15", "M16", "M17", "M19",
        "M20", "M21", "M18", "M22", "M24", "M25", "M26", "M29", "M30",
    ]


def test_canonical_networking_map_preserves_23_topics_and_seven_phases():
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    networking = next(track for track in payload["tracks"] if track["code"] == "NETWORKING")
    modules = [module for block in networking["blocks"] for module in block["modules"]]
    assert len(networking["blocks"]) == 7
    assert len(modules) == 23
    assert sum(module["hours"] for module in modules) == 214
    assert [block["code"] for block in networking["blocks"]] == [f"F{i}" for i in range(1, 8)]
    assert [module["source_module_code"] for block in networking["blocks"] for module in block["modules"]] == [f"{i:02d}" for i in range(1, 24)]


def test_curriculum_api_exposes_catalog_and_traceability_operations():
    schema = app.openapi()
    paths = schema["paths"]
    assert "/api/v1/curriculum/catalog" in paths
    assert "/api/v1/curriculum/tickets" in paths
    assert "/api/v1/curriculum/competencies/{competency_code}/traceability" in paths
    assert "/api/v1/curriculum/modules/{module_code}/topics" in paths
    assert "/api/v1/curriculum/modules/{module_code}/tickets" in paths
    assert "/api/v1/curriculum/modules/{module_code}/assessments" in paths
    assert "/api/v1/curriculum/evidence" in paths


def test_sqlalchemy_mappers_and_traceability_tables_are_valid():
    configure_mappers()
    expected = {
        "lesson_competencies", "lab_competencies", "ticket_competencies",
        "assessment_competencies", "competency_prerequisites",
    }
    assert expected.issubset(set(Base.metadata.tables))
