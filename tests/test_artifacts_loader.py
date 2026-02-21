from __future__ import annotations

import unittest
from pathlib import Path

from gtaf_sdk.artifacts import load_runtime_inputs
from gtaf_sdk.exceptions import (
    ArtifactNotFoundError,
    DuplicateArtifactIDError,
    InvalidDRCError,
    InvalidJSONError,
)


FIXTURES_ROOT = Path(__file__).parent / "fixtures" / "artifacts_loader"


class ArtifactLoaderTests(unittest.TestCase):
    def test_loads_runtime_inputs_happy_path(self) -> None:
        drc, artifacts = self._load("happy")

        self.assertIsInstance(drc, dict)
        self.assertEqual(list(artifacts.keys()), ["SB-001", "DR-001", "RB-001"])

    def test_missing_referenced_artifact_raises(self) -> None:
        with self.assertRaises(ArtifactNotFoundError):
            self._load("missing_artifact")

    def test_invalid_artifact_json_raises(self) -> None:
        with self.assertRaises(InvalidJSONError):
            self._load("invalid_artifact_json")

    def test_ignores_unreferenced_files(self) -> None:
        _, artifacts = self._load("no_scanning")

        self.assertEqual(list(artifacts.keys()), ["SB-001", "DR-001"])
        self.assertNotIn("SB-EXTRA", artifacts)

    def test_duplicate_across_categories_raises(self) -> None:
        with self.assertRaises(DuplicateArtifactIDError):
            self._load("duplicate_cross_category")

    def test_duplicate_within_category_is_deduped_preserving_order(self) -> None:
        _, artifacts = self._load("duplicate_within_category")

        self.assertEqual(list(artifacts.keys()), ["SB-001", "SB-002", "DR-001"])

    def test_drc_path_not_found_raises_invalid_drc(self) -> None:
        with self.assertRaises(InvalidDRCError):
            load_runtime_inputs(
                drc_path=str(FIXTURES_ROOT / "does_not_exist.json"),
                artifacts_dir=str(FIXTURES_ROOT / "happy" / "artifacts"),
            )

    def test_invalid_drc_json_raises(self) -> None:
        with self.assertRaises(InvalidJSONError):
            self._load("drc_invalid_json")

    def test_invalid_drc_structure_raises(self) -> None:
        with self.assertRaises(InvalidDRCError):
            self._load("drc_invalid_structure")

    def _load(self, case: str) -> tuple[dict, dict[str, dict]]:
        base = FIXTURES_ROOT / case
        return load_runtime_inputs(
            drc_path=str(base / "drc.json"),
            artifacts_dir=str(base / "artifacts"),
        )


if __name__ == "__main__":
    unittest.main()
