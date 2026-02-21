from __future__ import annotations

import unittest
from dataclasses import dataclass
from typing import Any
from unittest.mock import patch

from gtaf_sdk import enforcement
from gtaf_sdk.exceptions import (
    ArtifactNotFoundError,
    DuplicateArtifactIDError,
    InvalidArtifactError,
    InvalidDRCError,
    InvalidJSONError,
)


@dataclass(frozen=True)
class FakeEnforcementResult:
    outcome: str
    drc_id: str | None
    revision: int | None
    valid_until: str | None
    reason_code: str
    refs: list[str]
    details: dict[str, Any]


class EnforceFromFilesTests(unittest.TestCase):
    def setUp(self) -> None:
        enforcement._RUNTIME_INPUT_CACHE.clear()

    def test_happy_path_delegates_to_runtime(self) -> None:
        drc = {"id": "DRC-123"}
        artifacts = {"SB-1": {"id": "SB-1"}}
        context = {"action": "from-context", "scope": "ops.prod"}
        captured: dict[str, Any] = {}
        runtime_result = FakeEnforcementResult(
            outcome="EXECUTE",
            drc_id="DRC-123",
            revision=1,
            valid_until="2026-12-31T00:00:00Z",
            reason_code="OK",
            refs=["SB-1"],
            details={},
        )

        def fake_runtime_enforce(loaded_drc: dict, loaded_ctx: dict, loaded_artifacts: dict) -> FakeEnforcementResult:
            captured["drc"] = loaded_drc
            captured["ctx"] = loaded_ctx
            captured["artifacts"] = loaded_artifacts
            return runtime_result

        with (
            patch("gtaf_sdk.enforcement.load_runtime_inputs", return_value=(drc, artifacts)) as load_mock,
            patch("gtaf_sdk.enforcement._runtime_enforce", return_value=fake_runtime_enforce),
        ):
            result = enforcement.enforce_from_files(
                drc_path="/tmp/drc.json",
                artifacts_dir="/tmp/artifacts",
                context=context,
                action="override-action",
            )

        self.assertIs(result, runtime_result)
        load_mock.assert_called_once_with(
            drc_path="/tmp/drc.json",
            artifacts_dir="/tmp/artifacts",
            reload=False,
        )
        self.assertEqual(captured["drc"], drc)
        self.assertEqual(captured["artifacts"], artifacts)
        self.assertEqual(captured["ctx"]["action"], "override-action")
        self.assertEqual(context["action"], "from-context")

    def test_action_overrides_context_without_mutating_input(self) -> None:
        drc = {"id": "DRC-001"}
        artifacts = {"DR-1": {"id": "DR-1"}}
        context = {"action": "old-action", "scope": "ml.prod"}
        captured: dict[str, Any] = {}

        def fake_runtime_enforce(loaded_drc: dict, loaded_ctx: dict, loaded_artifacts: dict) -> FakeEnforcementResult:
            captured["drc"] = loaded_drc
            captured["ctx"] = loaded_ctx
            captured["artifacts"] = loaded_artifacts
            return FakeEnforcementResult(
                outcome="EXECUTE",
                drc_id="DRC-001",
                revision=1,
                valid_until="2026-12-31T00:00:00Z",
                reason_code="OK",
                refs=[],
                details={},
            )

        with (
            patch("gtaf_sdk.enforcement.load_runtime_inputs", return_value=(drc, artifacts)),
            patch("gtaf_sdk.enforcement._runtime_enforce", return_value=fake_runtime_enforce),
        ):
            enforcement.enforce_from_files(
                drc_path="/tmp/drc.json",
                artifacts_dir="/tmp/artifacts",
                context=context,
                action="new-action",
            )

        self.assertEqual(captured["ctx"]["action"], "new-action")
        self.assertEqual(context["action"], "old-action")

    def test_loader_errors_map_to_sdk_reason_codes(self) -> None:
        cases = [
            (InvalidDRCError("x"), "SDK_INVALID_DRC"),
            (ArtifactNotFoundError("x"), "SDK_ARTIFACT_NOT_FOUND"),
            (InvalidJSONError("x"), "SDK_INVALID_JSON"),
            (InvalidArtifactError("x"), "SDK_INVALID_ARTIFACT"),
            (DuplicateArtifactIDError("x"), "SDK_DUPLICATE_ARTIFACT_ID"),
            (RuntimeError("x"), "SDK_LOAD_ERROR"),
        ]

        for raised_error, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                with (
                    patch("gtaf_sdk.enforcement.load_runtime_inputs", side_effect=raised_error),
                    patch("gtaf_sdk.enforcement._runtime_result_class", return_value=FakeEnforcementResult),
                ):
                    result = enforcement.enforce_from_files(
                        drc_path="/tmp/drc.json",
                        artifacts_dir="/tmp/artifacts",
                        context={},
                    )

                self.assertEqual(result.outcome, "DENY")
                self.assertEqual(result.reason_code, expected_code)
                self.assertTrue(result.reason_code.startswith("SDK_"))
                self.assertIsNone(result.drc_id)
                self.assertIsNone(result.revision)
                self.assertIsNone(result.valid_until)
                self.assertEqual(result.refs, [])

    def test_cache_hit_reuses_loaded_inputs(self) -> None:
        drc = {"id": "DRC-001"}
        artifacts = {"SB-1": {"id": "SB-1"}}

        def fake_runtime_enforce(_drc: dict, _ctx: dict, _artifacts: dict) -> FakeEnforcementResult:
            return FakeEnforcementResult(
                outcome="EXECUTE",
                drc_id="DRC-001",
                revision=1,
                valid_until="2026-12-31T00:00:00Z",
                reason_code="OK",
                refs=[],
                details={},
            )

        with (
            patch("gtaf_sdk.enforcement.load_runtime_inputs", return_value=(drc, artifacts)) as load_mock,
            patch("gtaf_sdk.enforcement._runtime_enforce", return_value=fake_runtime_enforce),
        ):
            enforcement.enforce_from_files(
                drc_path="/tmp/drc.json",
                artifacts_dir="/tmp/artifacts",
                context={},
            )
            enforcement.enforce_from_files(
                drc_path="/tmp/drc.json",
                artifacts_dir="/tmp/artifacts",
                context={},
            )

        self.assertEqual(load_mock.call_count, 1)

    def test_reload_true_forces_reload(self) -> None:
        drc = {"id": "DRC-001"}
        artifacts = {"SB-1": {"id": "SB-1"}}

        def fake_runtime_enforce(_drc: dict, _ctx: dict, _artifacts: dict) -> FakeEnforcementResult:
            return FakeEnforcementResult(
                outcome="EXECUTE",
                drc_id="DRC-001",
                revision=1,
                valid_until="2026-12-31T00:00:00Z",
                reason_code="OK",
                refs=[],
                details={},
            )

        with (
            patch("gtaf_sdk.enforcement.load_runtime_inputs", return_value=(drc, artifacts)) as load_mock,
            patch("gtaf_sdk.enforcement._runtime_enforce", return_value=fake_runtime_enforce),
        ):
            enforcement.enforce_from_files(
                drc_path="/tmp/drc.json",
                artifacts_dir="/tmp/artifacts",
                context={},
            )
            enforcement.enforce_from_files(
                drc_path="/tmp/drc.json",
                artifacts_dir="/tmp/artifacts",
                context={},
                reload=True,
            )

        self.assertEqual(load_mock.call_count, 2)


if __name__ == "__main__":
    unittest.main()
