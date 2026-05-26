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

    def start(self):
        self._browser = launch(
            headless=BROWSER_HEADLESS,
            humanize=BROWSER_HUMANIZE,
            locale=BROWSER_LOCALE,
            timezone=BROWSER_TIMEZONE,
        )
        self._context = self._browser.new_context(viewport=BROWSER_VIEWPORT)
        self._page = self._context.new_page()
        return self._page

    def get_page(self):
        return self._page

    def new_page(self):
        self._page = self._context.new_page()
        return self._page

    def close(self):
        if self._browser:
            self._browser.close()
