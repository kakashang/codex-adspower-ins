from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import yaml


@dataclass
class AdsPowerConfig:
    api_base: str
    profile_id: str
    auto_create: bool
    group_id: str | None
    profile_name: str | None
    open_args: List[str]
    launch_timeout_sec: int


@dataclass
class InstagramConfig:
    username: str
    password: str
    target_username: str
    message: str
    login_timeout_sec: int


@dataclass
class GmailConfig:
    address: str
    password: str
    search_keywords: List[str]
    sender_keywords: List[str]
    confirm_keywords: List[str]
    link_host_keywords: List[str]
    poll_interval_sec: int
    poll_timeout_sec: int


@dataclass
class RuntimeConfig:
    headless: bool
    dry_run: bool


@dataclass
class AppConfig:
    adspower: AdsPowerConfig
    instagram: InstagramConfig
    gmail: GmailConfig
    runtime: RuntimeConfig


def _read_yaml(path: str | Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError("配置文件必须是 YAML 对象")
    return data


def _require(cfg: Dict[str, Any], key: str) -> Any:
    if key not in cfg or cfg[key] in (None, ""):
        raise ValueError(f"缺少必要配置: {key}")
    return cfg[key]


def load_config(path: str = "config.yaml") -> AppConfig:
    raw = _read_yaml(path)

    adsp = raw.get("adspower", {})
    ins = raw.get("instagram", {})
    gm = raw.get("gmail", {})
    runtime = raw.get("runtime", {})

    return AppConfig(
        adspower=AdsPowerConfig(
            api_base=_require(adsp, "api_base").rstrip("/"),
            profile_id=str(_require(adsp, "profile_id")),
            auto_create=bool(adsp.get("auto_create", False)),
            group_id=adsp.get("group_id"),
            profile_name=adsp.get("profile_name"),
            open_args=list(adsp.get("open_args", ["--disable-notifications"])),
            launch_timeout_sec=int(adsp.get("launch_timeout_sec", 60)),
        ),
        instagram=InstagramConfig(
            username=str(_require(ins, "username")),
            password=str(_require(ins, "password")),
            target_username=str(_require(ins, "target_username")),
            message=str(_require(ins, "message")),
            login_timeout_sec=int(ins.get("login_timeout_sec", 120)),
        ),
        gmail=GmailConfig(
            address=str(_require(gm, "address")),
            password=str(_require(gm, "password")),
            search_keywords=list(gm.get("search_keywords", ["Instagram", "Verify login", "It was me"])),
            sender_keywords=list(gm.get("sender_keywords", ["security@mail.instagram.com", "instagram", "meta"])),
            confirm_keywords=list(gm.get("confirm_keywords", ["It was me", "Verify", "Confirm", "This was me"])),
            link_host_keywords=list(gm.get("link_host_keywords", ["instagram.com", "accountscenter", "meta.com"])),
            poll_interval_sec=int(gm.get("poll_interval_sec", 10)),
            poll_timeout_sec=int(gm.get("poll_timeout_sec", 180)),
        ),
        runtime=RuntimeConfig(
            headless=bool(runtime.get("headless", False)),
            dry_run=bool(runtime.get("dry_run", False)),
        ),
    )
