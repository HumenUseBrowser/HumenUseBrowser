import os
from cloakbrowser import launch
from config import (
    BROWSER_HEADLESS, BROWSER_HUMANIZE, BROWSER_VIEWPORT,
    BROWSER_LOCALE, BROWSER_TIMEZONE,
)


class BrowserEngine:

    def __init__(self):
        self._browser = None
        self._context = None
        self._page = None
        self._har_path = None

    def start(self, har_path=None):
        self._browser = launch(
            headless=BROWSER_HEADLESS,
            humanize=BROWSER_HUMANIZE,
            locale=BROWSER_LOCALE,
            timezone=BROWSER_TIMEZONE,
        )
        self._context = self._browser.new_context(viewport=BROWSER_VIEWPORT)

        # Playwright 1.60.0: tracing.startHar()
        if har_path:
            self._har_path = har_path
            self._context.tracing.start(har_path=har_path, screenshots=True, snapshots=True)

        self._page = self._context.new_page()
        return self._page

    def get_page(self):
        return self._page

    def new_page(self):
        self._page = self._context.new_page()
        return self._page

    def stop_tracing(self, path=None):
        """停止 tracing 并保存"""
        if self._context:
            out = path or self._har_path
            if out:
                self._context.tracing.stop(path=out)
                print(f"  [Trace] Saved to {out}")

    def close(self):
        if self._har_path:
            self.stop_tracing()
        if self._browser:
            self._browser.close()
