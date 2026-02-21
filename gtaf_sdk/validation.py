from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .artifacts import load_runtime_inputs

SUPPORTED_GTAF_VERSIONS = {"0.1"}

SDK_VALIDATION_INVALID_DRC_STRUCTURE = "SDK_VALIDATION_INVALID_DRC_STRUCTURE"
SDK_VALIDATION_UNSUPPORTED_VERSION = "SDK_VALIDATION_UNSUPPORTED_VERSION"
SDK_VALIDATION_MISSING_REFERENCE = "SDK_VALIDATION_MISSING_REFERENCE"
SDK_VALIDATION_INVALID_TIMESTAMP = "SDK_VALIDATION_INVALID_TIMESTAMP"
SDK_VALIDATION_INVALID_TIME_WINDOW = "SDK_VALIDATION_INVALID_TIME_WINDOW"
SDK_VALIDATION_DUPLICATE_ARTIFACT_ID = "SDK_VALIDATION_DUPLICATE_ARTIFACT_ID"
SDK_VALIDATION_INVALID_ARTIFACT_STRUCTURE = "SDK_VALIDATION_INVALID_ARTIFACT_STRUCTURE"
SDK_VALIDATION_LOAD_ERROR = "SDK_VALIDATION_LOAD_ERROR"

_DUPLICATE_REF_ORDER = ("sb", "dr", "rb")
_ARTIFACT_REQUIRED_FIELDS = {
    "sb": ("scope", "included_components", "excluded_components", "allowed_interfaces"),
    "dr": ("scope", "decisions", "delegation_mode"),
    "rb": ("scope", "active"),
}


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    field_path: str | None
    artifact_id: str | None
    artifact_type: str | None


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: list[ValidationIssue]
    warnings: list[ValidationIssue]
    meta: dict[str, str] | None


def validate_artifacts(drc: dict, artifacts: dict[str, dict]) -> ValidationResult:
    errors: list[ValidationIssue] = []
    refs = {"sb": [], "dr": [], "rb": []}

    # 1) DRC structure checks.
    if not isinstance(drc, dict):
        _add_error(
            errors,
            code=SDK_VALIDATION_INVALID_DRC_STRUCTURE,
            message="drc must be an object",
            field_path="drc",
            artifact_id=None,
            artifact_type="drc",
        )
        drc_obj: dict[str, Any] = {}
    else:
        drc_obj = drc

    for field in ("id", "revision", "result", "gtaf_ref", "refs"):
        if field not in drc_obj:
            _add_error(
                errors,
                code=SDK_VALIDATION_INVALID_DRC_STRUCTURE,
                message=f"missing required field: {field}",
                field_path=f"drc.{field}",
                artifact_id=None,
                artifact_type="drc",
            )

    gtaf_ref = drc_obj.get("gtaf_ref")
    version: str | None = None
    if isinstance(gtaf_ref, dict):
        if "version" not in gtaf_ref:
            _add_error(
                errors,
                code=SDK_VALIDATION_INVALID_DRC_STRUCTURE,
                message="missing required field: gtaf_ref.version",
                field_path="drc.gtaf_ref.version",
                artifact_id=None,
                artifact_type="drc",
            )
        elif isinstance(gtaf_ref.get("version"), str) and gtaf_ref["version"]:
            version = gtaf_ref["version"]
        else:
            _add_error(
                errors,
                code=SDK_VALIDATION_INVALID_DRC_STRUCTURE,
                message="gtaf_ref.version must be a non-empty string",
                field_path="drc.gtaf_ref.version",
                artifact_id=None,
                artifact_type="drc",
            )
    else:
        _add_error(
            errors,
            code=SDK_VALIDATION_INVALID_DRC_STRUCTURE,
            message="gtaf_ref must be an object",
            field_path="drc.gtaf_ref",
            artifact_id=None,
            artifact_type="drc",
        )

    refs_obj = drc_obj.get("refs")
    if isinstance(refs_obj, dict):
        for category in ("sb", "dr", "rb"):
            ids = refs_obj.get(category)
            if not isinstance(ids, list):
                _add_error(
                    errors,
                    code=SDK_VALIDATION_INVALID_DRC_STRUCTURE,
                    message=f"refs.{category} must be a list",
                    field_path=f"drc.refs.{category}",
                    artifact_id=None,
                    artifact_type="drc",
                )
                continue
            for idx, item in enumerate(ids):
                if not isinstance(item, str) or not item:
                    _add_error(
                        errors,
                        code=SDK_VALIDATION_INVALID_DRC_STRUCTURE,
                        message=f"refs.{category} entries must be non-empty strings",
                        field_path=f"drc.refs.{category}[{idx}]",
                        artifact_id=None,
                        artifact_type="drc",
                    )
                    continue
                refs[category].append(item)
    else:
        _add_error(
            errors,
            code=SDK_VALIDATION_INVALID_DRC_STRUCTURE,
            message="refs must be an object",
            field_path="drc.refs",
            artifact_id=None,
            artifact_type="drc",
        )

    # 2) Version check.
    if version is not None and version not in SUPPORTED_GTAF_VERSIONS:
        _add_error(
            errors,
            code=SDK_VALIDATION_UNSUPPORTED_VERSION,
            message=f"unsupported gtaf_ref.version: {version}",
            field_path="drc.gtaf_ref.version",
            artifact_id=None,
            artifact_type="drc",
        )

    # 3) Reference completeness.
    for category in ("sb", "dr", "rb"):
        for idx, ref_id in enumerate(refs[category]):
            if ref_id not in artifacts:
                _add_error(
                    errors,
                    code=SDK_VALIDATION_MISSING_REFERENCE,
                    message="referenced artifact is missing",
                    field_path=f"drc.refs.{category}[{idx}]",
                    artifact_id=ref_id,
                    artifact_type=category,
                )

    # 4) Artifact structural checks.
    refs_by_id: dict[str, set[str]] = {}
    for category in ("sb", "dr", "rb"):
        for ref_id in refs[category]:
            refs_by_id.setdefault(ref_id, set()).add(category)

    seen_internal_ids: dict[str, str] = {}
    for artifact_key, artifact in artifacts.items():
        if not isinstance(artifact, dict):
            _add_error(
                errors,
                code=SDK_VALIDATION_INVALID_ARTIFACT_STRUCTURE,
                message="artifact must be an object",
                field_path=f"artifacts.{artifact_key}",
                artifact_id=artifact_key,
                artifact_type=_artifact_type_for_id(artifact_key, refs_by_id),
            )
            continue

        artifact_type = _artifact_type_for_id(artifact_key, refs_by_id)

        internal_id = artifact.get("id")
        if not isinstance(internal_id, str) or not internal_id:
            _add_error(
                errors,
                code=SDK_VALIDATION_INVALID_ARTIFACT_STRUCTURE,
                message="artifact.id must be a non-empty string",
                field_path=f"artifacts.{artifact_key}.id",
                artifact_id=artifact_key,
                artifact_type=artifact_type,
            )
        else:
            if internal_id != artifact_key:
                _add_error(
                    errors,
                    code=SDK_VALIDATION_DUPLICATE_ARTIFACT_ID,
                    message="artifact key and artifact.id must match",
                    field_path=f"artifacts.{artifact_key}.id",
                    artifact_id=artifact_key,
                    artifact_type=artifact_type,
                )
            previous_key = seen_internal_ids.get(internal_id)
            if previous_key is not None and previous_key != artifact_key:
                _add_error(
                    errors,
                    code=SDK_VALIDATION_DUPLICATE_ARTIFACT_ID,
                    message="duplicate artifact.id value",
                    field_path=f"artifacts.{artifact_key}.id",
                    artifact_id=artifact_key,
                    artifact_type=artifact_type,
                )
            else:
                seen_internal_ids[internal_id] = artifact_key

        if artifact_type in _ARTIFACT_REQUIRED_FIELDS:
            for field in _ARTIFACT_REQUIRED_FIELDS[artifact_type]:
                if field not in artifact:
                    _add_error(
                        errors,
                        code=SDK_VALIDATION_INVALID_ARTIFACT_STRUCTURE,
                        message=f"missing required field: {field}",
                        field_path=f"artifacts.{artifact_key}.{field}",
                        artifact_id=artifact_key,
                        artifact_type=artifact_type,
                    )

        if "linked_scopes" in artifact and not isinstance(artifact.get("linked_scopes"), list):
            _add_error(
                errors,
                code=SDK_VALIDATION_INVALID_ARTIFACT_STRUCTURE,
                message="linked_scopes must be a list when present",
                field_path=f"artifacts.{artifact_key}.linked_scopes",
                artifact_id=artifact_key,
                artifact_type=artifact_type,
            )

    # 5) Timestamp sanity checks.
    _validate_timestamp_fields(
        errors=errors,
        entity=drc_obj,
        entity_path="drc",
        artifact_id=None,
        artifact_type="drc",
    )
    for artifact_key, artifact in artifacts.items():
        if isinstance(artifact, dict):
            _validate_timestamp_fields(
                errors=errors,
                entity=artifact,
                entity_path=f"artifacts.{artifact_key}",
                artifact_id=artifact_key,
                artifact_type=_artifact_type_for_id(artifact_key, refs_by_id),
            )

    return ValidationResult(
        ok=len(errors) == 0,
        errors=errors,
        warnings=[],
        meta=None,
    )


def warmup_from_files(
    drc_path: str,
    artifacts_dir: str,
    reload: bool = False,
) -> ValidationResult:
    try:
        drc, artifacts = load_runtime_inputs(
            drc_path=drc_path,
            artifacts_dir=artifacts_dir,
            reload=reload,
        )
    except Exception as exc:
        return ValidationResult(
            ok=False,
            errors=[
                ValidationIssue(
                    code=SDK_VALIDATION_LOAD_ERROR,
                    message="failed to load runtime inputs",
                    field_path=None,
                    artifact_id=None,
                    artifact_type=None,
                )
            ],
            warnings=[],
            meta={
                "drc_path": drc_path,
                "artifacts_dir": artifacts_dir,
                "error": str(exc),
            },
        )

    result = validate_artifacts(drc=drc, artifacts=artifacts)
    return ValidationResult(
        ok=result.ok,
        errors=result.errors,
        warnings=result.warnings,
        meta={"drc_path": drc_path, "artifacts_dir": artifacts_dir},
    )


def _artifact_type_for_id(ref_id: str, refs_by_id: dict[str, set[str]]) -> str | None:
    categories = refs_by_id.get(ref_id, set())
    if len(categories) == 1:
        for category in _DUPLICATE_REF_ORDER:
            if category in categories:
                return category
    return None


def _validate_timestamp_fields(
    *,
    errors: list[ValidationIssue],
    entity: dict[str, Any],
    entity_path: str,
    artifact_id: str | None,
    artifact_type: str | None,
) -> None:
    start_raw = entity.get("valid_from")
    end_raw = entity.get("valid_until")

    start = None
    end = None
    if "valid_from" in entity:
        start = _parse_datetime(start_raw)
        if start is None:
            _add_error(
                errors,
                code=SDK_VALIDATION_INVALID_TIMESTAMP,
                message="valid_from must be a valid datetime",
                field_path=f"{entity_path}.valid_from",
                artifact_id=artifact_id,
                artifact_type=artifact_type,
            )
    if "valid_until" in entity:
        end = _parse_datetime(end_raw)
        if end is None:
            _add_error(
                errors,
                code=SDK_VALIDATION_INVALID_TIMESTAMP,
                message="valid_until must be a valid datetime",
                field_path=f"{entity_path}.valid_until",
                artifact_id=artifact_id,
                artifact_type=artifact_type,
            )

    if start is not None and end is not None and not start < end:
        _add_error(
            errors,
            code=SDK_VALIDATION_INVALID_TIME_WINDOW,
            message="valid_from must be earlier than valid_until",
            field_path=entity_path,
            artifact_id=artifact_id,
            artifact_type=artifact_type,
        )


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _add_error(
    errors: list[ValidationIssue],
    *,
    code: str,
    message: str,
    field_path: str | None,
    artifact_id: str | None,
    artifact_type: str | None,
) -> None:
    errors.append(
        ValidationIssue(
            code=code,
            message=message,
            field_path=field_path,
            artifact_id=artifact_id,
            artifact_type=artifact_type,
        )
    )
