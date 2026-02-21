from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class TelemetryHooks:
    on_enforcement_start: Callable[[dict], None] | None = None
    on_enforcement_end: Callable[[dict], None] | None = None
