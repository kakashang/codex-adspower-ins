from __future__ import annotations

import logging
import time

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from utils.config import InstagramConfig


class InstagramLogin:
    LOGIN_URL = "https://www.instagram.com/accounts/login/"

    def __init__(self, page: Page, config: InstagramConfig, logger: logging.Logger):
        self.page = page
        self.config = config
        self.logger = logger

    def login(self) -> str:
        self.logger.info("打开 Instagram 登录页")
        self.page.goto(self.LOGIN_URL, wait_until="domcontentloaded", timeout=90000)
        self._dismiss_popups()

        self.logger.info("输入账号密码")
        self.page.locator("input[name='username']").first.fill(self.config.username, timeout=30000)
        self.page.locator("input[name='password']").first.fill(self.config.password, timeout=30000)
        self.page.locator("button[type='submit']").first.click()

        return self._wait_login_result()

    def _wait_login_result(self) -> str:
        deadline = time.time() + self.config.login_timeout_sec
        while time.time() < deadline:
            self.page.wait_for_timeout(1500)
            url = self.page.url.lower()
            content = self.page.content().lower()

            if "/challenge" in url or "confirm it's you" in content or "check your email" in content:
                self.logger.info("检测到登录挑战/邮箱验证")
                return "email_challenge"
            if "two_factor" in url or "security code" in content:
                self.logger.warning("检测到二次验证码流程，当前版本未自动处理")
                return "2fa_required"
            if "instagram.com" in url and "/accounts/login" not in url and "login" not in url.split("?")[0][-12:]:
                self.logger.info("Instagram 登录成功，当前 URL: %s", url)
                self._dismiss_popups()
                return "success"
            if "incorrect" in content or "wrong password" in content:
                return "bad_credentials"

        raise TimeoutError("等待 Instagram 登录结果超时")

    def _dismiss_popups(self) -> None:
        for text in ["Not Now", "稍后再说", "Save info", "Turn on Notifications"]:
            try:
                btn = self.page.get_by_role("button", name=text)
                if btn.count() > 0:
                    btn.first.click(timeout=1500)
                    self.logger.info("关闭弹窗: %s", text)
            except PlaywrightTimeoutError:
                pass
            except Exception:
                pass
