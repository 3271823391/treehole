# AI 树洞（FastAPI）

## 项目简介

AI 树洞是一个面向心理倾诉与情绪陪伴场景的轻量型对话应用，强调“可持续演进的产品结构”和“清晰的工程边界”。它基于 FastAPI 提供服务，前端为原生 HTML/CSS/JavaScript，支持流式对话、用户中心与基础记忆持久化。

## 用户身份与记忆机制

- **用户名即身份标识**：系统以用户名派生用户标识。
  - 规则：`user_id = "u_" + sha1(username.trim().toLowerCase())`
- **用户名与聊天记忆绑定**：所有对话历史与记忆均与 `user_id` 关联。
- **修改用户名会切换到新的对话记忆**：因为 `user_id` 发生变化，会进入另一套全新的对话历史。
- **本地缓存**：浏览器使用 `localStorage` 保存 `last_username`，刷新后可恢复上一次使用的用户名。

## 用户中心功能

- **自定义用户名**：作为用户身份标识，影响 `user_id` 与对话记忆归属。
- **显示名称**：用于界面展示（优先显示显示名称，没有则显示用户名）。
- **自定义头像**：上传后即刻更新头像展示，并绑定到当前用户档案。
- **跨刷新/跨设备恢复**：只要使用相同用户名，即可恢复该身份下的历史记录与头像。

## 头像与数据存储

- 头像文件存储在：`static/avatars`。
- 用户档案与对话数据存储在本地 JSON 文件（`user_data.json`）。
- 当前版本为**无账号系统**方案，不包含 PIN 或注册流程。

## 技术栈

- **后端**：FastAPI
- **前端**：原生 HTML / CSS / JavaScript（直接由 FastAPI 渲染页面）
- **大模型**：DeepSeek Chat API
- **存储**：本地 JSON 文件（用户数据、对话历史、记忆）

## 已知限制与设计取舍

- **用户名即身份**：无独立账号系统，用户名即会话身份与记忆索引。
- **无注册与权限管理**：该版本不提供登录、权限或 PIN 机制。
- **本地存储为默认方案**：数据保存在本地 JSON 文件与静态目录，适合原型验证与私有部署；如需多用户或线上部署，需要引入数据库与对象存储。

## 快速开始

1. 创建虚拟环境并安装依赖

```bash
python -m venv venv
source venv/bin/activate  # Windows 使用 venv\Scripts\activate
pip install -r requirements.txt
```

2. 配置环境变量（`.env`）

```bash
DEEPSEEK_API_KEY=你的_API_KEY
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_API_URL=https://api.deepseek.com/chat/completions
PORT=8000
```

3. 启动项目

```bash
python run.py
```

浏览器访问：`http://localhost:8000`
