from __future__ import annotations

from typing import Literal

from .exceptions import ActionNormalizationError

UNKNOWN_ACTION_ID = "__unknown__"


def normalize_action(
    *,
    tool_name: str | None = None,
    arguments: dict | None = None,
    mapping: dict[str, str] | None = None,
    command_argument_keys: tuple[str, ...] = ("command", "cmd"),
    on_unknown: Literal["return_unknown", "raise"] = "return_unknown",
) -> str:
    normalized_tool = _normalize_tool_name(tool_name)
    if normalized_tool is None:
        return _handle_unknown("tool_name missing", on_unknown)

    if mapping is None:
        return _handle_unknown("mapping missing", on_unknown)

    prefix = mapping.get(normalized_tool)
    if not isinstance(prefix, str) or not prefix:
        return _handle_unknown("tool_name not mapped", on_unknown)

    command = _extract_command(arguments=arguments, keys=command_argument_keys)
    if command is None:
        return prefix

    first_token = _first_token(command)
    if first_token is None:
        return _handle_unknown("command invalid", on_unknown)

    return f"{prefix}.{first_token}"


def _normalize_tool_name(tool_name: str | None) -> str | None:
    if tool_name is None:
        return None
    normalized = tool_name.strip().lower()
    if not normalized:
        return None
    return normalized


def _extract_command(*, arguments: dict | None, keys: tuple[str, ...]) -> str | None:
    if arguments is None:
        return None
    if not isinstance(arguments, dict):
        return ""
    for key in keys:
        if key in arguments:
            value = arguments[key]
            if isinstance(value, str):
                return value
            return ""
    return None


def _first_token(command: str) -> str | None:
    tokens = command.strip().split()
    if not tokens:
        return None
    return tokens[0]


def _handle_unknown(reason: str, on_unknown: str) -> str:
    if on_unknown == "return_unknown":
        return UNKNOWN_ACTION_ID
    if on_unknown == "raise":
        raise ActionNormalizationError(f"unknown_action: {reason}")
    raise ActionNormalizationError("unknown_action: invalid on_unknown mode")
