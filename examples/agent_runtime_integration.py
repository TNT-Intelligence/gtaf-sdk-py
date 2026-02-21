from __future__ import annotations

from gtaf_sdk.actions import normalize_action
from gtaf_sdk.enforcement import enforce_from_files
from gtaf_sdk.models import RuntimeContext
from gtaf_sdk.telemetry import TelemetryHooks


def _execute_tool(tool_name: str, arguments: dict) -> dict:
    return {"ok": True, "tool": tool_name, "arguments": arguments}


def _deny_response(result) -> dict:
    return {
        "ok": False,
        "outcome": result.outcome,
        "reason_code": result.reason_code,
        "refs": result.refs,
    }


def run_agent_step(
    *,
    drc_path: str,
    artifacts_dir: str,
    tool_name: str,
    arguments: dict,
    mapping: dict[str, str],
    hooks: TelemetryHooks | None = None,
) -> dict:
    action_id = normalize_action(
        tool_name=tool_name,
        arguments=arguments,
        mapping=mapping,
    )
    context = RuntimeContext(
        scope="ops.prod",
        component="ops.agent",
        interface="ops-api",
        action=action_id,
    ).to_dict()

    result = enforce_from_files(
        drc_path=drc_path,
        artifacts_dir=artifacts_dir,
        context=context,
        hooks=hooks,
    )
    if result.outcome == "DENY":
        return _deny_response(result)

    return _execute_tool(tool_name, arguments)


if __name__ == "__main__":
    hooks = TelemetryHooks(
        on_enforcement_start=lambda payload: print("start:", payload),
        on_enforcement_end=lambda payload: print("end:", payload),
    )
    response = run_agent_step(
        drc_path="path/to/drc.json",
        artifacts_dir="path/to/artifacts",
        tool_name="Git",
        arguments={"command": "status"},
        mapping={"git": "git"},
        hooks=hooks,
    )
    print(response)
