from __future__ import annotations

from typing import Any


class DeniedActionError(Exception):
    def __init__(self, result: Any) -> None:
        self.result = result
        super().__init__(f"action denied: reason_code={getattr(result, 'reason_code', None)}")


class EnforcementUnavailableError(Exception):
    pass
