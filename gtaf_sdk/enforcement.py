from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .artifacts import load_runtime_inputs
from .exceptions import (
    ArtifactNotFoundError,
    DuplicateArtifactIDError,
    InvalidArtifactError,
    InvalidDRCError,
    InvalidJSONError,
)

if TYPE_CHECKING:
    from gtaf_runtime.types import EnforcementResult


_RUNTIME_INPUT_CACHE: dict[tuple[str, str], tuple[dict, dict[str, dict]]] = {}


def enforce_from_files(
    *,
    drc_path: str,
    artifacts_dir: str,
    context: dict,
    action: str | None = None,
    reload: bool = False,
) -> "EnforcementResult":
    ctx = dict(context)
    if action is not None:
        ctx["action"] = action

    cache_key = (drc_path, artifacts_dir)

    try:
        if not reload and cache_key in _RUNTIME_INPUT_CACHE:
            drc, artifacts = _RUNTIME_INPUT_CACHE[cache_key]
        else:
            drc, artifacts = load_runtime_inputs(
                drc_path=drc_path,
                artifacts_dir=artifacts_dir,
                reload=reload,
            )
            _RUNTIME_INPUT_CACHE[cache_key] = (drc, artifacts)
    except InvalidDRCError as exc:
        return _sdk_deny("SDK_INVALID_DRC", drc_path=drc_path, artifacts_dir=artifacts_dir, error=str(exc))
    except ArtifactNotFoundError as exc:
        return _sdk_deny(
            "SDK_ARTIFACT_NOT_FOUND",
            drc_path=drc_path,
            artifacts_dir=artifacts_dir,
            error=str(exc),
        )
    except InvalidJSONError as exc:
        return _sdk_deny("SDK_INVALID_JSON", drc_path=drc_path, artifacts_dir=artifacts_dir, error=str(exc))
    except InvalidArtifactError as exc:
        return _sdk_deny(
            "SDK_INVALID_ARTIFACT",
            drc_path=drc_path,
            artifacts_dir=artifacts_dir,
            error=str(exc),
        )
    except DuplicateArtifactIDError as exc:
        return _sdk_deny(
            "SDK_DUPLICATE_ARTIFACT_ID",
            drc_path=drc_path,
            artifacts_dir=artifacts_dir,
            error=str(exc),
        )
    except Exception as exc:
        return _sdk_deny("SDK_LOAD_ERROR", drc_path=drc_path, artifacts_dir=artifacts_dir, error=str(exc))

    enforce = _runtime_enforce()
    return enforce(drc, ctx, artifacts)


def _sdk_deny(reason_code: str, *, drc_path: str, artifacts_dir: str, error: str) -> "EnforcementResult":
    if not reason_code.startswith("SDK_"):
        raise ValueError("SDK deny reason codes must start with 'SDK_'")

    result_cls = _runtime_result_class()
    return result_cls(
        outcome="DENY",
        drc_id=None,
        revision=None,
        valid_until=None,
        reason_code=reason_code,
        refs=[],
        details={
            "drc_path": drc_path,
            "artifacts_dir": artifacts_dir,
            "error": error,
        },
    )


def _runtime_enforce():
    from gtaf_runtime import enforce

    return enforce


def _runtime_result_class():
    from gtaf_runtime.types import EnforcementResult

    return EnforcementResult
