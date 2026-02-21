from __future__ import annotations

import unittest
from dataclasses import dataclass
from typing import Any
from unittest.mock import patch

from gtaf_sdk import enforcement
from gtaf_sdk.telemetry import TelemetryHooks


@dataclass(frozen=True)
class FakeEnforcementResult:
    outcome: str
    drc_id: str | None
    revision: int | None
    valid_until: str | None
    reason_code: str
    refs: list[str]
    details: dict[str, Any]


class TelemetryHooksTests(unittest.TestCase):
    def setUp(self) -> None:
        enforcement._RUNTIME_INPUT_CACHE.clear()

    def test_hooks_receive_payload_for_runtime_result(self) -> None:
        start_payloads: list[dict] = []
        end_payloads: list[dict] = []
        hooks = TelemetryHooks(
            on_enforcement_start=lambda payload: start_payloads.append(payload),
            on_enforcement_end=lambda payload: end_payloads.append(payload),
        )
        runtime_result = FakeEnforcementResult(
            outcome="EXECUTE",
            drc_id="DRC-001",
            revision=3,
            valid_until="2026-12-31T00:00:00Z",
            reason_code="OK",
            refs=["SB-001", "DR-001"],
            details={},
        )

        with (
            patch("gtaf_sdk.enforcement.load_runtime_inputs", return_value=({"id": "DRC-001"}, {})),
            patch("gtaf_sdk.enforcement._runtime_enforce", return_value=lambda *_: runtime_result),
        ):
            result = enforcement.enforce_from_files(
                drc_path="/tmp/drc.json",
                artifacts_dir="/tmp/artifacts",
                context={
                    "action": "git.commit",
                    "scope": "ops.prod",
                    "component": "ops.agent",
                    "interface": "ops-api",
                },
                hooks=hooks,
            )

        self.assertIs(result, runtime_result)
        self.assertEqual(len(start_payloads), 1)
        self.assertEqual(len(end_payloads), 1)
        self.assertEqual(
            start_payloads[0],
            {
                "action": "git.commit",
                "scope": "ops.prod",
                "component": "ops.agent",
                "interface": "ops-api",
                "drc_path": "/tmp/drc.json",
                "artifacts_dir": "/tmp/artifacts",
            },
        )
        self.assertEqual(
            end_payloads[0],
            {
                "action": "git.commit",
                "scope": "ops.prod",
                "component": "ops.agent",
                "interface": "ops-api",
                "drc_path": "/tmp/drc.json",
                "artifacts_dir": "/tmp/artifacts",
                "outcome": "EXECUTE",
                "reason_code": "OK",
                "refs": ("SB-001", "DR-001"),
                "drc_id": "DRC-001",
                "revision": 3,
                "valid_until": "2026-12-31T00:00:00Z",
            },
        )

    def test_hooks_receive_payload_for_sdk_prefixed_deny(self) -> None:
        end_payloads: list[dict] = []
        hooks = TelemetryHooks(on_enforcement_end=lambda payload: end_payloads.append(payload))

        with (
            patch("gtaf_sdk.enforcement.load_runtime_inputs", side_effect=RuntimeError("load failed")),
            patch("gtaf_sdk.enforcement._runtime_result_class", return_value=FakeEnforcementResult),
        ):
            result = enforcement.enforce_from_files(
                drc_path="/tmp/drc.json",
                artifacts_dir="/tmp/artifacts",
                context={"action": "git.commit"},
                hooks=hooks,
            )

        self.assertEqual(result.outcome, "DENY")
        self.assertTrue(result.reason_code.startswith("SDK_"))
        self.assertEqual(len(end_payloads), 1)
        self.assertEqual(end_payloads[0]["reason_code"], result.reason_code)
        self.assertEqual(end_payloads[0]["outcome"], "DENY")

    def test_hook_exceptions_are_swallowed(self) -> None:
        runtime_result = FakeEnforcementResult(
            outcome="EXECUTE",
            drc_id="DRC-001",
            revision=1,
            valid_until="2026-12-31T00:00:00Z",
            reason_code="OK",
            refs=[],
            details={},
        )
        hooks = TelemetryHooks(
            on_enforcement_start=lambda _payload: (_ for _ in ()).throw(RuntimeError("start hook failed")),
            on_enforcement_end=lambda _payload: (_ for _ in ()).throw(RuntimeError("end hook failed")),
        )

        with (
            patch("gtaf_sdk.enforcement.load_runtime_inputs", return_value=({"id": "DRC-001"}, {})),
            patch("gtaf_sdk.enforcement._runtime_enforce", return_value=lambda *_: runtime_result),
        ):
            result = enforcement.enforce_from_files(
                drc_path="/tmp/drc.json",
                artifacts_dir="/tmp/artifacts",
                context={},
                hooks=hooks,
            )

        self.assertIs(result, runtime_result)


if __name__ == "__main__":
    unittest.main()
