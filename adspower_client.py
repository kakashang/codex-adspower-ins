from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests


@dataclass
class BrowserLaunchInfo:
    ws_endpoint: str
    debugger_address: str
    profile_id: str


class AdsPowerClient:
    def __init__(self, api_base: str, logger: logging.Logger, timeout_sec: int = 30):
        self.api_base = api_base.rstrip("/")
        self.logger = logger
        self.timeout_sec = timeout_sec

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.api_base}{path}"
        self.logger.info("调用 AdsPower GET: %s", url)
        resp = requests.get(url, params=params or {}, timeout=self.timeout_sec)
        resp.raise_for_status()
        data = resp.json()
        self._ensure_success(data)
        return data

    def _post(self, path: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.api_base}{path}"
        self.logger.info("调用 AdsPower POST: %s", url)
        resp = requests.post(url, json=payload or {}, timeout=self.timeout_sec)
        resp.raise_for_status()
        data = resp.json()
        self._ensure_success(data)
        return data

    def _ensure_success(self, data: Dict[str, Any]) -> None:
        code = data.get("code")
        status = data.get("status")
        if code not in (0, "0") and status not in ("success", "ok", 0, "0", None):
            raise RuntimeError(f"AdsPower 接口失败: {data}")

    def create_profile(self, group_id: str, profile_name: str) -> str:
        payload = {
            "group_id": group_id,
            "user_proxy_config": {"proxy_soft": "no_proxy"},
            "name": profile_name,
        }
        data = self._post("/api/v1/user/create", payload)
        user_id = str(data.get("data", {}).get("id") or data.get("data", {}).get("user_id"))
        if not user_id:
            raise RuntimeError(f"创建环境成功但未返回 id: {data}")
        self.logger.info("创建 AdsPower 环境成功: %s", user_id)
        return user_id

    def start_browser(self, profile_id: str, launch_args: Optional[list[str]] = None) -> BrowserLaunchInfo:
        params = {
            "user_id": profile_id,
            "ip_tab": 0,
            "headless": 0,
            "launch_args": " ".join(launch_args or []),
        }
        data = self._get("/api/v1/browser/start", params=params)
        d = data.get("data", {})
        ws_endpoint = (
            d.get("ws", {}).get("puppeteer")
            or d.get("ws", {}).get("selenium")
            or d.get("ws")
            or d.get("webdriver")
        )
        debugger_address = d.get("debug_port") or d.get("ws", {}).get("http") or ""

        if not ws_endpoint:
            raise RuntimeError(f"未获取到 ws 调试地址: {data}")

        self.logger.info("AdsPower 浏览器启动成功, profile=%s, ws=%s", profile_id, ws_endpoint)
        return BrowserLaunchInfo(
            ws_endpoint=ws_endpoint,
            debugger_address=str(debugger_address),
            profile_id=profile_id,
        )

    def stop_browser(self, profile_id: str) -> None:
        try:
            self._get("/api/v1/browser/stop", params={"user_id": profile_id})
            self.logger.info("AdsPower 浏览器已关闭: %s", profile_id)
        except Exception:
            self.logger.exception("关闭 AdsPower 浏览器失败: %s", profile_id)
