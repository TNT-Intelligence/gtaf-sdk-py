from __future__ import annotations

import unittest

from gtaf_sdk.models import ActionId, RuntimeContext


class ModelsTests(unittest.TestCase):
    def test_action_id_to_str_returns_exact_value(self) -> None:
        action = ActionId(value="Git.Commit")

        self.assertEqual(action.to_str(), "Git.Commit")

    def test_runtime_context_to_dict_core_keys_only_and_order(self) -> None:
        context = RuntimeContext(
            scope="ops.prod",
            component="ops.agent",
            interface="ops-api",
            action="git.commit",
        )

        result = context.to_dict()

        self.assertEqual(
            result,
            {
                "scope": "ops.prod",
                "component": "ops.agent",
                "interface": "ops-api",
                "action": "git.commit",
            },
        )
        self.assertEqual(list(result.keys()), ["scope", "component", "interface", "action"])

    def test_runtime_context_to_dict_appends_extras_deterministically(self) -> None:
        extras = {"system": "rachel-ai", "mode": "ci", "user": "tim"}
        context = RuntimeContext(
            scope="ops.prod",
            component="ops.agent",
            interface="ops-api",
            action="git.commit",
            extras=extras,
        )

        result = context.to_dict()

        self.assertEqual(
            list(result.keys()),
            ["scope", "component", "interface", "action", "system", "mode", "user"],
        )
        self.assertEqual(result["system"], "rachel-ai")
        self.assertEqual(result["mode"], "ci")
        self.assertEqual(result["user"], "tim")

    def test_runtime_context_to_dict_extras_collision_raises_stable_message(self) -> None:
        context = RuntimeContext(
            scope="ops.prod",
            component="ops.agent",
            interface="ops-api",
            action="git.commit",
            extras={"scope": "override"},
        )

        with self.assertRaisesRegex(ValueError, r"^extras contains reserved key: scope$"):
            context.to_dict()

    def test_runtime_context_to_dict_does_not_mutate_extras(self) -> None:
        extras = {"system": "rachel-ai", "mode": "ci"}
        before = dict(extras)
        context = RuntimeContext(
            scope="ops.prod",
            component="ops.agent",
            interface="ops-api",
            action="git.commit",
            extras=extras,
        )

        _ = context.to_dict()

        self.assertEqual(extras, before)

    def test_runtime_context_to_dict_preserves_whitespace_and_case(self) -> None:
        context = RuntimeContext(
            scope=" Ops.Prod ",
            component="Ops.Agent",
            interface=" Ops-API ",
            action=" Git.Commit ",
            extras={"mode": " CI "},
        )

        result = context.to_dict()

        self.assertEqual(result["scope"], " Ops.Prod ")
        self.assertEqual(result["component"], "Ops.Agent")
        self.assertEqual(result["interface"], " Ops-API ")
        self.assertEqual(result["action"], " Git.Commit ")
        self.assertEqual(result["mode"], " CI ")


if __name__ == "__main__":
    unittest.main()
