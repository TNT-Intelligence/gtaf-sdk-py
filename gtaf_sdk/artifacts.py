from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .exceptions import (
    ArtifactNotFoundError,
    DuplicateArtifactIDError,
    InvalidArtifactError,
    InvalidDRCError,
    InvalidJSONError,
)


def load_runtime_inputs(
    drc_path: str,
    artifacts_dir: str,
    *,
    reload: bool = False,
) -> tuple[dict, dict[str, dict]]:
    """
    Loads a DRC projection and resolves referenced SB/DR/RB artifact projections
    deterministically from disk, returning runtime-compatible inputs.
    """
    del reload  # Forward-compatible API; caching is intentionally not implemented yet.

    drc_file = Path(drc_path)
    if not drc_file.is_file():
        raise InvalidDRCError(
            f"drc_not_found: missing drc file (id='', category='drc', path='{drc_file}')"
        )

    drc = _load_json_file(drc_file, category="drc")
    refs = _validate_drc_refs(drc, drc_file)

    root_dir = Path(artifacts_dir)
    artifacts_by_id: dict[str, dict] = {}

    for category in ("sb", "dr", "rb"):
        seen_in_category: set[str] = set()
        for artifact_id in refs[category]:
            if artifact_id in seen_in_category:
                continue
            seen_in_category.add(artifact_id)

            artifact_path = root_dir / category / f"{artifact_id}.json"
            if not artifact_path.is_file():
                raise ArtifactNotFoundError(
                    "artifact_not_found: missing referenced artifact "
                    f"(id='{artifact_id}', category='{category}', path='{artifact_path}')"
                )

            if artifact_id in artifacts_by_id:
                raise DuplicateArtifactIDError(
                    "duplicate_artifact_id: referenced across categories "
                    f"(id='{artifact_id}', category='{category}', path='{artifact_path}')"
                )

            artifact = _load_json_file(artifact_path, category=category)
            if not isinstance(artifact, dict):
                raise InvalidArtifactError(
                    "invalid_artifact: expected object "
                    f"(id='{artifact_id}', category='{category}', path='{artifact_path}')"
                )

            artifact_obj_id = artifact.get("id")
            if artifact_obj_id is not None and artifact_obj_id != artifact_id:
                raise InvalidArtifactError(
                    "invalid_artifact: id mismatch "
                    f"(id='{artifact_id}', category='{category}', path='{artifact_path}')"
                )

            artifacts_by_id[artifact_id] = artifact

    return drc, artifacts_by_id


def _load_json_file(path: Path, *, category: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise InvalidJSONError(
            "invalid_json: failed to parse json "
            f"(id='{path.stem}', category='{category}', path='{path}')"
        ) from exc


def _validate_drc_refs(drc: Any, drc_file: Path) -> dict[str, list[str]]:
    if not isinstance(drc, dict):
        raise InvalidDRCError(
            f"invalid_drc: expected object (id='', category='drc', path='{drc_file}')"
        )

    refs = drc.get("refs")
    if not isinstance(refs, dict):
        raise InvalidDRCError(
            f"invalid_drc: refs missing (id='', category='drc', path='{drc_file}')"
        )

    required_groups = ("sb", "dr", "rb")
    for group in required_groups:
        if group not in refs:
            raise InvalidDRCError(
                f"invalid_drc: refs.{group} missing (id='', category='drc', path='{drc_file}')"
            )
        if not isinstance(refs[group], list):
            raise InvalidDRCError(
                f"invalid_drc: refs.{group} invalid (id='', category='drc', path='{drc_file}')"
            )

    if len(refs["sb"]) < 1 or len(refs["dr"]) < 1:
        raise InvalidDRCError(
            f"invalid_drc: refs cardinality invalid (id='', category='drc', path='{drc_file}')"
        )

    normalized: dict[str, list[str]] = {"sb": [], "dr": [], "rb": []}
    for group in required_groups:
        for item in refs[group]:
            if not isinstance(item, str) or not item:
                raise InvalidDRCError(
                    f"invalid_drc: refs.{group} id invalid (id='', category='drc', path='{drc_file}')"
                )
            normalized[group].append(item)

    return normalized
