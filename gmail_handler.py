from __future__ import annotations

import logging
import time
from urllib.parse import urlparse

from playwright.sync_api import BrowserContext, Page

from utils.config import GmailConfig


class GmailHandler:
    def __init__(self, context: BrowserContext, config: GmailConfig, logger: logging.Logger):
        self.context = context
        self.config = config
        self.logger = logger

    def confirm_instagram_login(self) -> bool:
        page = self.context.new_page()
        try:
            self._ensure_gmail_ready(page)
            return self._poll_and_confirm(page)
        finally:
            page.close()

    def _ensure_gmail_ready(self, page: Page) -> None:
        self.logger.info("打开 Gmail")
        page.goto("https://mail.google.com/mail/u/0/#inbox", wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(3000)

        if "accounts.google.com" in page.url:
            self.logger.info("检测到 Gmail 未登录，尝试自动登录")
            page.locator("input[type='email']").first.fill(self.config.address)
            page.get_by_role("button", name="Next").first.click()
            page.wait_for_timeout(1500)
            page.locator("input[type='password']").first.fill(self.config.password)
            page.get_by_role("button", name="Next").first.click()
            page.wait_for_url("**mail.google.com/**", timeout=60000)

    def _poll_and_confirm(self, page: Page) -> bool:
        query = " OR ".join(self.config.search_keywords)
        deadline = time.time() + self.config.poll_timeout_sec

        while time.time() < deadline:
            self.logger.info("检索 Gmail 邮件: %s", query)
            page.goto(
                f"https://mail.google.com/mail/u/0/#search/{query}",
                wait_until="domcontentloaded",
                timeout=90000,
            )
            page.wait_for_timeout(3000)

            rows = page.locator("tr.zA")
            if rows.count() == 0:
                self.logger.info("暂无匹配邮件，等待 %s 秒", self.config.poll_interval_sec)
                page.wait_for_timeout(self.config.poll_interval_sec * 1000)
                continue

            rows.first.click()
            page.wait_for_timeout(2000)
            if self._is_expected_sender(page):
                link = self._extract_confirm_link(page)
                if link:
                    self.logger.info("提取到确认链接: %s", link)
                    page.goto(link, wait_until="domcontentloaded", timeout=90000)
                    return True
            self.logger.info("当前邮件不匹配确认条件，继续轮询")
            page.go_back()
            page.wait_for_timeout(self.config.poll_interval_sec * 1000)

        self.logger.error("Gmail 邮件确认超时")
        return False

    def _is_expected_sender(self, page: Page) -> bool:
        content = page.content().lower()
        return any(k.lower() in content for k in self.config.sender_keywords)

    def _extract_confirm_link(self, page: Page) -> str | None:
        anchors = page.locator("a[href]")
        for i in range(anchors.count()):
            href = anchors.nth(i).get_attribute("href") or ""
            text = (anchors.nth(i).inner_text() or "").strip().lower()
            if not href.startswith("http"):
                continue
            host = urlparse(href).netloc.lower()
            host_ok = any(k.lower() in host for k in self.config.link_host_keywords)
            text_ok = any(k.lower() in text for k in self.config.confirm_keywords)
            if host_ok and text_ok:
                return href
        return None
