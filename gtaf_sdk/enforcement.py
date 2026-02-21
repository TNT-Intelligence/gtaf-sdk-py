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
from .telemetry import TelemetryHooks

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
    hooks: TelemetryHooks | None = None,
) -> "EnforcementResult":
    ctx = dict(context)
    if action is not None:
        ctx["action"] = action

    _maybe_call_hook(
        hooks,
        "on_enforcement_start",
        {
            "action": ctx.get("action"),
            "scope": ctx.get("scope"),
            "component": ctx.get("component"),
            "interface": ctx.get("interface"),
            "drc_path": drc_path,
            "artifacts_dir": artifacts_dir,
        },
    )

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
        result = _sdk_deny("SDK_INVALID_DRC", drc_path=drc_path, artifacts_dir=artifacts_dir, error=str(exc))
        _maybe_call_end_hook(hooks, ctx, drc_path, artifacts_dir, result)
        return result
    except ArtifactNotFoundError as exc:
        result = _sdk_deny(
            "SDK_ARTIFACT_NOT_FOUND",
            drc_path=drc_path,
            artifacts_dir=artifacts_dir,
            error=str(exc),
        )
        _maybe_call_end_hook(hooks, ctx, drc_path, artifacts_dir, result)
        return result
    except InvalidJSONError as exc:
        result = _sdk_deny("SDK_INVALID_JSON", drc_path=drc_path, artifacts_dir=artifacts_dir, error=str(exc))
        _maybe_call_end_hook(hooks, ctx, drc_path, artifacts_dir, result)
        return result
    except InvalidArtifactError as exc:
        result = _sdk_deny(
            "SDK_INVALID_ARTIFACT",
            drc_path=drc_path,
            artifacts_dir=artifacts_dir,
            error=str(exc),
        )
        _maybe_call_end_hook(hooks, ctx, drc_path, artifacts_dir, result)
        return result
    except DuplicateArtifactIDError as exc:
        result = _sdk_deny(
            "SDK_DUPLICATE_ARTIFACT_ID",
            drc_path=drc_path,
            artifacts_dir=artifacts_dir,
            error=str(exc),
        )
        _maybe_call_end_hook(hooks, ctx, drc_path, artifacts_dir, result)
        return result
    except Exception as exc:
        result = _sdk_deny("SDK_LOAD_ERROR", drc_path=drc_path, artifacts_dir=artifacts_dir, error=str(exc))
        _maybe_call_end_hook(hooks, ctx, drc_path, artifacts_dir, result)
        return result

    enforce = _runtime_enforce()
    result = enforce(drc, ctx, artifacts)
    _maybe_call_end_hook(hooks, ctx, drc_path, artifacts_dir, result)
    return result


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


def _maybe_call_end_hook(
    hooks: Any,
    ctx: dict,
    drc_path: str,
    artifacts_dir: str,
    result: Any,
) -> None:
    refs_value = getattr(result, "refs", None)
    if isinstance(refs_value, list):
        refs_payload = tuple(refs_value)
    elif isinstance(refs_value, tuple):
        refs_payload = refs_value
    else:
        refs_payload = refs_value

    _maybe_call_hook(
        hooks,
        "on_enforcement_end",
        {
            "action": ctx.get("action"),
            "scope": ctx.get("scope"),
            "component": ctx.get("component"),
            "interface": ctx.get("interface"),
            "drc_path": drc_path,
            "artifacts_dir": artifacts_dir,
            "outcome": getattr(result, "outcome", None),
            "reason_code": getattr(result, "reason_code", None),
            "refs": refs_payload,
            "drc_id": getattr(result, "drc_id", None),
            "revision": getattr(result, "revision", None),
            "valid_until": getattr(result, "valid_until", None),
        },
    )


def _maybe_call_hook(hooks: Any, hook_name: str, payload: dict) -> None:
    if hooks is None:
        return
    try:
        hook = getattr(hooks, hook_name)
        if hook is not None:
            hook(payload)
    except Exception:
        return
