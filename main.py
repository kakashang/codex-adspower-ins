from __future__ import annotations

import argparse

from adspower_client import AdsPowerClient
from browser_manager import BrowserManager
from gmail_handler import GmailHandler
from instagram_login import InstagramLogin
from instagram_messenger import InstagramMessenger
from utils.config import load_config
from utils.logger import setup_logger


def run(config_path: str) -> int:
    config = load_config(config_path)
    logger = setup_logger()

    adspower = AdsPowerClient(config.adspower.api_base, logger)
    profile_id = config.adspower.profile_id

    if config.adspower.auto_create:
        if not config.adspower.group_id or not config.adspower.profile_name:
            raise ValueError("auto_create=True 时必须配置 group_id 与 profile_name")
        profile_id = adspower.create_profile(config.adspower.group_id, config.adspower.profile_name)

    session = None
    try:
        launch_info = adspower.start_browser(profile_id, config.adspower.open_args)
        browser_manager = BrowserManager(logger)
        session = browser_manager.connect_via_cdp(launch_info.ws_endpoint)

        login = InstagramLogin(session.page, config.instagram, logger)
        login_result = login.login()
        logger.info("Instagram 登录结果: %s", login_result)

        if login_result == "email_challenge":
            gmail = GmailHandler(session.context, config.gmail, logger)
            if not gmail.confirm_instagram_login():
                logger.error("Gmail 登录确认失败")
                return 2
            session.page.reload(wait_until="domcontentloaded")
            login_result = login._wait_login_result()
            logger.info("邮件确认后二次检测登录结果: %s", login_result)

        if login_result != "success":
            logger.error("登录失败，中止流程: %s", login_result)
            return 3

        messenger = InstagramMessenger(session.page, logger)
        ok, reason = messenger.send_message(
            config.instagram.target_username,
            config.instagram.message,
        )
        if not ok:
            logger.error("私信发送失败: %s", reason)
            return 4

        logger.info("流程执行成功: %s", reason)
        return 0
    finally:
        if session:
            BrowserManager(logger).close(session)
        adspower.stop_browser(profile_id)


def main() -> None:
    parser = argparse.ArgumentParser(description="AdsPower + Instagram 自动登录与私信")
    parser.add_argument("-c", "--config", default="config.yaml", help="配置文件路径")
    args = parser.parse_args()
    raise SystemExit(run(args.config))


if __name__ == "__main__":
    main()
