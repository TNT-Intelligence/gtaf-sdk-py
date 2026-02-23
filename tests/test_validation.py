from __future__ import annotations

import unittest
from unittest.mock import patch

from gtaf_sdk.validation import (
    SDK_VALIDATION_INVALID_DRC_STRUCTURE,
    SDK_VALIDATION_DUPLICATE_ARTIFACT_ID,
    SDK_VALIDATION_INVALID_TIME_WINDOW,
    SDK_VALIDATION_INVALID_TIMESTAMP,
    SDK_VALIDATION_LOAD_ERROR,
    SDK_VALIDATION_MISSING_REFERENCE,
    SDK_VALIDATION_UNSUPPORTED_VERSION,
    validate_artifacts,
    warmup_from_files,
)


def _valid_drc() -> dict:
    return {
        "id": "DRC-001",
        "revision": 1,
        "result": "PERMITTED",
        "gtaf_ref": {"version": "0.1"},
        "refs": {
            "sb": ["SB-001"],
            "dr": ["DR-001"],
            "rb": ["RB-001"],
        },
        "valid_from": "2026-01-01T00:00:00Z",
        "valid_until": "2026-12-31T00:00:00Z",
    }


def _valid_artifacts() -> dict[str, dict]:
    return {
        "SB-001": {
            "id": "SB-001",
            "scope": "ops.prod",
            "included_components": ["ops.agent"],
            "excluded_components": [],
            "allowed_interfaces": ["ops-api"],
            "valid_from": "2026-01-01T00:00:00Z",
            "valid_until": "2026-12-31T00:00:00Z",
        },
        "DR-001": {
            "id": "DR-001",
            "scope": "ops.prod",
            "decisions": ["restart_worker"],
            "delegation_mode": "AUTONOMOUS",
            "valid_from": "2026-01-01T00:00:00Z",
            "valid_until": "2026-12-31T00:00:00Z",
        },
        "RB-001": {
            "id": "RB-001",
            "scope": "ops.prod",
            "active": True,
            "valid_from": "2026-01-01T00:00:00Z",
            "valid_until": "2026-12-31T00:00:00Z",
        },
    }


class ValidationTests(unittest.TestCase):
    def _validate(
        self,
        drc: dict,
        artifacts: dict[str, dict],
        *,
        runtime_schema_ok: bool = True,
        supported_versions: set[str] | None = None,
    ):
        if supported_versions is None:
            supported_versions = {"0.1"}
        with (
            patch("gtaf_sdk.validation._runtime_validate_drc_schema", return_value=runtime_schema_ok),
            patch("gtaf_sdk.validation._runtime_supported_versions", return_value=supported_versions),
        ):
            return validate_artifacts(drc, artifacts)

    def test_valid_inputs_return_ok(self) -> None:
        result = self._validate(_valid_drc(), _valid_artifacts())

        self.assertTrue(result.ok)
        self.assertEqual(result.errors, [])

    def test_missing_reference_returns_error_code(self) -> None:
        artifacts = _valid_artifacts()
        del artifacts["DR-001"]

        result = self._validate(_valid_drc(), artifacts)

        self.assertFalse(result.ok)
        self.assertIn(SDK_VALIDATION_MISSING_REFERENCE, [issue.code for issue in result.errors])

    def test_unsupported_version_returns_error_code(self) -> None:
        drc = _valid_drc()
        drc["gtaf_ref"]["version"] = "9.9"

        result = self._validate(drc, _valid_artifacts(), supported_versions={"0.1"})

        self.assertFalse(result.ok)
        self.assertIn(SDK_VALIDATION_UNSUPPORTED_VERSION, [issue.code for issue in result.errors])

    def test_invalid_timestamp_returns_error_code(self) -> None:
        drc = _valid_drc()
        drc["valid_from"] = "not-a-timestamp"

        result = self._validate(drc, _valid_artifacts(), runtime_schema_ok=False)

        self.assertFalse(result.ok)
        self.assertIn(SDK_VALIDATION_INVALID_TIMESTAMP, [issue.code for issue in result.errors])

    def test_invalid_window_order_returns_error_code(self) -> None:
        artifacts = _valid_artifacts()
        artifacts["RB-001"]["valid_from"] = "2026-12-31T00:00:00Z"
        artifacts["RB-001"]["valid_until"] = "2026-01-01T00:00:00Z"

        result = self._validate(_valid_drc(), artifacts)

        self.assertFalse(result.ok)
        self.assertIn(SDK_VALIDATION_INVALID_TIME_WINDOW, [issue.code for issue in result.errors])

    def test_duplicate_artifact_id_returns_error_code(self) -> None:
        artifacts = _valid_artifacts()
        artifacts["DR-001"]["id"] = "SB-001"

        result = self._validate(_valid_drc(), artifacts)

        self.assertFalse(result.ok)
        self.assertIn(SDK_VALIDATION_DUPLICATE_ARTIFACT_ID, [issue.code for issue in result.errors])

    def test_warmup_loader_failure_maps_to_load_error(self) -> None:
        with patch("gtaf_sdk.validation.load_runtime_inputs", side_effect=RuntimeError("boom")):
            result = warmup_from_files(
                drc_path="/tmp/drc.json",
                artifacts_dir="/tmp/artifacts",
            )

        self.assertFalse(result.ok)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].code, SDK_VALIDATION_LOAD_ERROR)

    def test_parity_ok_true_implies_runtime_structural_acceptance(self) -> None:
        result = self._validate(_valid_drc(), _valid_artifacts(), runtime_schema_ok=True)

        self.assertTrue(result.ok)
        self.assertNotIn(SDK_VALIDATION_INVALID_DRC_STRUCTURE, [issue.code for issue in result.errors])

    def test_parity_runtime_structural_reject_fails_in_sdk(self) -> None:
        result = self._validate(_valid_drc(), _valid_artifacts(), runtime_schema_ok=False)

        self.assertFalse(result.ok)
        self.assertIn(SDK_VALIDATION_INVALID_DRC_STRUCTURE, [issue.code for issue in result.errors])


if __name__ == "__main__":
    unittest.main()
