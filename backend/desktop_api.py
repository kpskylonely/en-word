from __future__ import annotations

import sys
from typing import Any, Callable

WINDOW_TITLE = "离线背单词"


class DesktopApi:
    def __init__(self) -> None:
        self.window: Any = None

    def bind_window(self, window: Any) -> None:
        self.window = window

    def init_desktop_window(self, stealth_mode: bool) -> dict[str, bool]:
        if self.window is None:
            return {"ok": False, "supported": False}
        try:
            self._schedule_frameless(bool(stealth_mode))
            return {"ok": True, "supported": True}
        except Exception:
            return {"ok": False, "supported": False}

    def set_stealth_mode(self, enabled: bool, always_on_top: bool = True) -> dict[str, bool]:
        if self.window is None:
            return {"ok": False, "supported": False}

        try:
            self.window.on_top = bool(enabled and always_on_top)
            self._schedule_frameless(bool(enabled))
            return {"ok": True, "supported": True}
        except Exception:
            return {"ok": False, "supported": False}

    def _schedule_frameless(self, stealth: bool) -> None:
        self.window.frameless = True
        self._run_on_main_thread(lambda: self._apply_frameless(stealth))

    def _run_on_main_thread(self, callback: Callable[[], None]) -> None:
        if sys.platform == "darwin":
            from PyObjCTools import AppHelper

            AppHelper.callAfter(callback)
            return

        callback()

    def _apply_frameless(self, stealth: bool) -> None:
        if sys.platform == "darwin":
            self._apply_frameless_macos(stealth)
        elif sys.platform.startswith("linux"):
            self._apply_frameless_gtk(stealth)
        elif sys.platform == "win32":
            self._apply_frameless_win32(stealth)

        if hasattr(self.window, "set_title"):
            self.window.set_title("")

    def _native_window(self) -> Any | None:
        return getattr(self.window, "native", None)

    def _apply_frameless_macos(self, stealth: bool) -> None:
        import AppKit

        native = self._native_window()
        if native is None:
            return

        try:
            title_hidden = AppKit.NSWindowTitleHidden
        except AttributeError:
            title_hidden = 1

        # Integrated frameless chrome: native title never shown; app draws the header.
        native.setTitle_("")
        native.setTitlebarAppearsTransparent_(True)
        native.setTitleVisibility_(title_hidden)

        for button_type in (
            AppKit.NSWindowCloseButton,
            AppKit.NSWindowMiniaturizeButton,
            AppKit.NSWindowZoomButton,
        ):
            button = native.standardWindowButton_(button_type)
            if button is not None:
                button.setHidden_(stealth)

    def _apply_frameless_gtk(self, stealth: bool) -> None:
        native = self._native_window()
        if native is not None:
            native.set_decorated(not stealth)

    def _apply_frameless_win32(self, stealth: bool) -> None:
        native = self._native_window()
        if native is None:
            return

        form_border_style = getattr(native, "FormBorderStyle", None)
        if form_border_style is None:
            return

        none_style = getattr(form_border_style, "None", None)
        sizable_style = getattr(form_border_style, "Sizable", None)
        if none_style is None or sizable_style is None:
            return

        native.FormBorderStyle = none_style if stealth else sizable_style
