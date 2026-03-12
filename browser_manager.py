from __future__ import annotations

import logging
from dataclasses import dataclass

from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright


@dataclass
class BrowserSession:
    playwright: Playwright
    browser: Browser
    context: BrowserContext
    page: Page


class BrowserManager:
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def connect_via_cdp(self, ws_endpoint: str) -> BrowserSession:
        self.logger.info("通过 CDP 接管浏览器: %s", ws_endpoint)
        pw = sync_playwright().start()
        browser = pw.chromium.connect_over_cdp(ws_endpoint)
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = context.pages[0] if context.pages else context.new_page()
        return BrowserSession(playwright=pw, browser=browser, context=context, page=page)

    def close(self, session: BrowserSession) -> None:
        try:
            session.browser.close()
        except Exception:
            self.logger.exception("关闭浏览器连接失败")
        finally:
            session.playwright.stop()
