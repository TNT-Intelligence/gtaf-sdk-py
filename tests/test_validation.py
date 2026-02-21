from __future__ import annotations

import unittest
from unittest.mock import patch

from gtaf_sdk.validation import (
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
    def test_valid_inputs_return_ok(self) -> None:
        result = validate_artifacts(_valid_drc(), _valid_artifacts())

        self.assertTrue(result.ok)
        self.assertEqual(result.errors, [])

    def test_missing_reference_returns_error_code(self) -> None:
        artifacts = _valid_artifacts()
        del artifacts["DR-001"]

        result = validate_artifacts(_valid_drc(), artifacts)

        self.assertFalse(result.ok)
        self.assertIn(SDK_VALIDATION_MISSING_REFERENCE, [issue.code for issue in result.errors])

    def test_unsupported_version_returns_error_code(self) -> None:
        drc = _valid_drc()
        drc["gtaf_ref"]["version"] = "9.9"

        result = validate_artifacts(drc, _valid_artifacts())

        self.assertFalse(result.ok)
        self.assertIn(SDK_VALIDATION_UNSUPPORTED_VERSION, [issue.code for issue in result.errors])

    def test_invalid_timestamp_returns_error_code(self) -> None:
        drc = _valid_drc()
        drc["valid_from"] = "not-a-timestamp"

        result = validate_artifacts(drc, _valid_artifacts())

        self.assertFalse(result.ok)
        self.assertIn(SDK_VALIDATION_INVALID_TIMESTAMP, [issue.code for issue in result.errors])

    def test_invalid_window_order_returns_error_code(self) -> None:
        artifacts = _valid_artifacts()
        artifacts["RB-001"]["valid_from"] = "2026-12-31T00:00:00Z"
        artifacts["RB-001"]["valid_until"] = "2026-01-01T00:00:00Z"

        result = validate_artifacts(_valid_drc(), artifacts)

        self.assertFalse(result.ok)
        self.assertIn(SDK_VALIDATION_INVALID_TIME_WINDOW, [issue.code for issue in result.errors])

    def test_duplicate_artifact_id_returns_error_code(self) -> None:
        artifacts = _valid_artifacts()
        artifacts["DR-001"]["id"] = "SB-001"

        result = validate_artifacts(_valid_drc(), artifacts)

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


if __name__ == "__main__":
    unittest.main()
