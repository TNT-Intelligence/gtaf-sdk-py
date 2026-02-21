from __future__ import annotations

import unittest

from gtaf_sdk.actions import UNKNOWN_ACTION_ID, normalize_action
from gtaf_sdk.exceptions import ActionNormalizationError


class ActionNormalizationTests(unittest.TestCase):
    def test_known_tool_without_command_returns_prefix(self) -> None:
        result = normalize_action(
            tool_name="git",
            arguments=None,
            mapping={"git": "git"},
        )
        self.assertEqual(result, "git")

    def test_known_tool_with_command_returns_prefix_and_first_token(self) -> None:
        result = normalize_action(
            tool_name="git",
            arguments={"command": "commit -m msg"},
            mapping={"git": "git"},
        )
        self.assertEqual(result, "git.commit")

    def test_first_token_only_is_used(self) -> None:
        result = normalize_action(
            tool_name="git",
            arguments={"command": "push origin main"},
            mapping={"git": "git"},
        )
        self.assertEqual(result, "git.push")

    def test_whitespace_and_case_normalization_is_stable(self) -> None:
        result = normalize_action(
            tool_name="  Git  ",
            arguments={"command": "   commit   -m msg"},
            mapping={"git": "git"},
        )
        self.assertEqual(result, "git.commit")

    def test_unknown_tool_returns_unknown_action_id(self) -> None:
        result = normalize_action(
            tool_name="jira",
            arguments={"command": "transition ISSUE-1"},
            mapping={"git": "git"},
        )
        self.assertEqual(result, UNKNOWN_ACTION_ID)

    def test_unknown_tool_with_strict_mode_raises(self) -> None:
        with self.assertRaises(ActionNormalizationError):
            normalize_action(
                tool_name="jira",
                arguments={"command": "transition ISSUE-1"},
                mapping={"git": "git"},
                on_unknown="raise",
            )

    def test_no_mapping_provided_returns_unknown(self) -> None:
        result = normalize_action(
            tool_name="git",
            arguments={"command": "status"},
            mapping=None,
        )
        self.assertEqual(result, UNKNOWN_ACTION_ID)

    def test_identical_inputs_produce_identical_output(self) -> None:
        kwargs = {
            "tool_name": "git",
            "arguments": {"command": "status --short"},
            "mapping": {"git": "git"},
        }
        first = normalize_action(**kwargs)
        second = normalize_action(**kwargs)
        self.assertEqual(first, second)

    def test_no_implicit_tool_name_prefix_fallback(self) -> None:
        result = normalize_action(
            tool_name="custom_tool",
            arguments={"command": "run"},
            mapping={"git": "git"},
        )
        self.assertEqual(result, UNKNOWN_ACTION_ID)


if __name__ == "__main__":
    unittest.main()
