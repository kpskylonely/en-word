from __future__ import annotations

from typing import Any


class DesktopApi:
    def __init__(self) -> None:
        self.window: Any = None

    def bind_window(self, window: Any) -> None:
        self.window = window

    def set_stealth_mode(self, enabled: bool, always_on_top: bool = True) -> dict[str, bool]:
        if self.window is None:
            return {"ok": False, "supported": False}

        try:
            self.window.on_top = bool(enabled and always_on_top)
        except Exception:
            return {"ok": False, "supported": False}

        return {"ok": True, "supported": True}
