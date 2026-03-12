from __future__ import annotations

import logging

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError


class InstagramMessenger:
    def __init__(self, page: Page, logger: logging.Logger):
        self.page = page
        self.logger = logger

    def send_message(self, target_username: str, message: str) -> tuple[bool, str]:
        try:
            self._dismiss_popups()
            target_url = f"https://www.instagram.com/{target_username}/"
            self.logger.info("打开目标用户主页: %s", target_url)
            self.page.goto(target_url, wait_until="domcontentloaded", timeout=90000)

            if "sorry, this page isn't available" in self.page.content().lower():
                return False, "目标用户不存在或不可见"

            if not self._open_message_entry():
                return False, "无法打开私信入口（可能目标账号不支持私信）"

            box = self.page.locator("textarea[placeholder*='Message'], div[role='textbox']").first
            box.wait_for(timeout=15000)
            box.click()
            box.fill(message)

            send_btn = self.page.get_by_role("button", name="Send")
            if send_btn.count() > 0:
                send_btn.first.click()
            else:
                box.press("Enter")

            self.logger.info("私信发送完成")
            return True, "发送成功"

        except PlaywrightTimeoutError:
            self.logger.exception("发送私信超时")
            return False, "页面加载超时"
        except Exception as exc:
            self.logger.exception("发送私信失败")
            return False, f"异常: {exc}"

    def _open_message_entry(self) -> bool:
        for name in ["Message", "发消息", "发送消息"]:
            btn = self.page.get_by_role("button", name=name)
            if btn.count() > 0:
                btn.first.click()
                self.page.wait_for_timeout(2000)
                return True

        direct_link = self.page.locator("a[href*='/direct/t/']")
        if direct_link.count() > 0:
            direct_link.first.click()
            self.page.wait_for_timeout(2000)
            return True
        return False

    def _dismiss_popups(self) -> None:
        for text in ["Not Now", "稍后再说", "Allow all cookies", "Only allow essential cookies"]:
            try:
                btn = self.page.get_by_role("button", name=text)
                if btn.count() > 0:
                    btn.first.click(timeout=1000)
            except Exception:
                pass
