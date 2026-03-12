# AdsPower + Gmail + Instagram 浏览器自动化项目（Python）

本项目通过 **AdsPower 浏览器环境** + **Playwright 浏览器自动化**，实现以下流程：

1. 启动/接管 AdsPower 指定浏览器环境
2. 打开 Instagram 并执行账号登录
3. 若触发邮箱确认，自动进入 Gmail 检索并执行确认链接
4. 登录成功后进入目标用户主页并发送私信

> 注意：本项目**不调用 Instagram 官方 API**，全部通过网页自动化实现。

---

## 1. 环境依赖

- Python 3.11+
- 本地已安装并运行 AdsPower 客户端
- 可访问 Instagram / Gmail 的网络环境

---

## 2. 安装步骤

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

---

## 3. AdsPower 前置准备

1. 打开 AdsPower 客户端并保持运行
2. 在 AdsPower 中准备好一个浏览器环境（或启用自动创建）
3. 确认本地 API 地址（默认常见是 `http://127.0.0.1:50325`）
4. 获取目标浏览器环境的 `profile_id`

---

## 4. 配置方法

复制配置文件并填写真实参数：

```bash
cp config.example.yaml config.yaml
```

关键配置说明：

- `adspower.api_base`：AdsPower 本地 API 地址
- `adspower.profile_id`：要启动/复用的 AdsPower 环境 ID
- `instagram.username/password`：Instagram 登录账号
- `gmail.address/password`：Gmail 账号（建议使用 App Password）
- `instagram.target_username`：目标用户
- `instagram.message`：要发送的私信内容
- `gmail.search_keywords/sender_keywords/...`：邮件检索与确认规则

---

## 5. 启动方法

```bash
python main.py -c config.yaml
```

程序返回码：

- `0`：执行成功
- `2`：Gmail 邮件确认失败
- `3`：Instagram 登录失败
- `4`：私信发送失败

---

## 6. 项目结构

```text
.
├── main.py
├── adspower_client.py
├── browser_manager.py
├── instagram_login.py
├── gmail_handler.py
├── instagram_messenger.py
├── requirements.txt
├── config.example.yaml
├── README.md
├── logs/
└── utils/
    ├── config.py
    └── logger.py
```

---

## 7. 常见问题

### Q1: AdsPower 接口调用失败

- 检查 AdsPower 是否正在运行
- 检查 `api_base` 是否正确
- 检查 `profile_id` 是否存在并可启动

### Q2: Instagram 登录后仍停留在挑战页

- 可能触发额外风控（如短信/APP 二次验证）
- 当前版本已支持 Gmail 邮件确认，但不含短信 OTP 自动输入

### Q3: Gmail 找不到确认邮件

- 增大 `gmail.poll_timeout_sec`
- 调整 `search_keywords/sender_keywords/confirm_keywords`
- 检查 Gmail 是否触发了新设备登录验证

### Q4: 无法发送私信

- 目标用户可能关闭了私信入口
- 目标用户不存在或不可见
- 账号触发了 Instagram 限制

---

## 8. 日志说明

- 日志文件路径：`logs/run.log`
- 记录内容包含：
  - AdsPower 启动结果
  - Instagram 登录步骤与结果
  - Gmail 检索与确认结果
  - 目标用户搜索/打开结果
  - 私信发送结果与失败原因

---

## 9. 安全建议

- 不要把真实账号密码提交到 Git 仓库
- 建议仅在受控测试账号上验证
- 建议配合代理/IP 管理与行为频率控制，避免触发风控
