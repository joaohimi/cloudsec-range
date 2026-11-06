"""Idempotently import the source-verified Linux and Networking roadmap."""
import json
from pathlib import Path

from sqlalchemy import select

from app.db.session import get_session_factory
from app.models import CurriculumBlock, CurriculumModule, CurriculumTrack, CurriculumVersion, Lab


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_CANDIDATES = [
    Path("/workspace-content/curriculum/canonical-roadmap-v1.json"),
    ROOT / "content" / "curriculum" / "canonical-roadmap-v1.json",
    ROOT.parent.parent / "content" / "curriculum" / "canonical-roadmap-v1.json",
]
MANIFEST = next((candidate for candidate in MANIFEST_CANDIDATES if candidate.is_file()), MANIFEST_CANDIDATES[0])
SOURCE = "Cronograma de estudo — Redes e Linux (1).pdf"


def seed() -> dict[str, int]:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    Session = get_session_factory()
    created = {"versions": 0, "tracks": 0, "blocks": 0, "modules": 0, "labs": 0}

    with Session.begin() as db:
        version_data = payload["version"]
        version = db.scalar(select(CurriculumVersion).where(CurriculumVersion.code == version_data["code"]))
        if version is None:
            version = CurriculumVersion(
                code=version_data["code"], title=version_data["title"],
                source_filename=version_data["source_filename"], status=version_data["status"],
                import_notes=version_data.get("notes"),
            )
            db.add(version)
            db.flush()
            created["versions"] += 1
        else:
            version.title = version_data["title"]
            version.source_filename = version_data["source_filename"]
            version.status = version_data["status"]
            version.import_notes = version_data.get("notes")

        for track_data in payload["tracks"]:
            track = db.scalar(select(CurriculumTrack).where(CurriculumTrack.code == track_data["code"]))
            if track is None:
                track = CurriculumTrack(
                    code=track_data["code"], title=track_data["title"],
                    description=track_data.get("description"), position=track_data["position"],
                    version_id=version.id, is_active=True,
                )
                db.add(track)
                db.flush()
                created["tracks"] += 1
            else:
                track.title = track_data["title"]
                track.description = track_data.get("description")
                track.position = track_data["position"]
                track.version_id = version.id
                track.is_active = True

            module_position = 0
            for block_data in track_data["blocks"]:
                block = db.scalar(
                    select(CurriculumBlock).where(
                        CurriculumBlock.track_id == track.id,
                        CurriculumBlock.code == block_data["code"],
                    )
                )
                if block is None:
                    block = CurriculumBlock(
                        track_id=track.id, code=block_data["code"],
                        title=block_data["code"], position=block_data["position"],
                    )
                    db.add(block)
                    db.flush()
                    created["blocks"] += 1
                else:
                    block.title = block_data["code"]
                    block.position = block_data["position"]

                for module_data in block_data["modules"]:
                    module_position += 1
                    source_code = module_data["source_module_code"]
                    normalized_code = source_code[1:].zfill(2) if source_code.startswith("M") else source_code.zfill(2)
                    module_code = f"{track.code}-{normalized_code}"
                    module = db.scalar(select(CurriculumModule).where(CurriculumModule.code == module_code))
                    fields = dict(
                        track_id=track.id, block_id=block.id, source_module_code=source_code,
                        title=module_data["title"], position=module_position,
                        estimated_hours=module_data["hours"], canonical_source=SOURCE,
                        source_verified=True,
                    )
                    if module is None:
                        module = CurriculumModule(
                            code=module_code, content_status="not_authored", **fields
                        )
                        db.add(module)
                        created["modules"] += 1
                    else:
                        for key, value in fields.items():
                            setattr(module, key, value)

            lab_data = track_data.get("blocks", [])
            for block_data in lab_data:
                env_lab = block_data.get("environment_lab")
                if not env_lab:
                    continue
                lab = db.scalar(select(Lab).where(Lab.code == env_lab["code"]))
                lab_fields = dict(
                    track_id=track.id, module_id=None, title=env_lab["title"],
                    description=env_lab["description"], environment="WSL2 Ubuntu 24.04",
                    safety_profile="local-safe", estimated_minutes=env_lab["hours"] * 60,
                    manifest={"source": SOURCE, "scope": "local-lab-setup"}, status="planned",
                )
                if lab is None:
                    db.add(Lab(code=env_lab["code"], **lab_fields))
                    created["labs"] += 1
                else:
                    for key, value in lab_fields.items():
                        setattr(lab, key, value)

    return created


if __name__ == "__main__":
    from app.scripts.seed_linux_m01 import seed as seed_linux_m01

    print(json.dumps({"canonical_roadmap": seed(), "linux_l1_m01": seed_linux_m01()}, ensure_ascii=False, indent=2))
