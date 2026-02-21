from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ActionId:
    value: str

    def to_str(self) -> str:
        return self.value


@dataclass(frozen=True)
class RuntimeContext:
    scope: str
    component: str
    interface: str
    action: str
    extras: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "scope": self.scope,
            "component": self.component,
            "interface": self.interface,
            "action": self.action,
        }

        if self.extras is None:
            return result

        collision_keys = ("scope", "component", "interface", "action")
        for key in collision_keys:
            if key in self.extras:
                raise ValueError(f"extras contains reserved key: {key}")

        for key, value in self.extras.items():
            result[key] = value

        return result
