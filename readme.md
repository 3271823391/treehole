virtual-treehole-deepseek

一个基于 FastAPI + DeepSeek 的本地运行虚拟树洞项目，支持 AI 性格定制 / 风格克隆 / 流式聊天 / 简易长期记忆。项目目标不是炫技，而是构建一个结构清晰、可持续演进的陪伴型对话系统。

✨ 项目特性

🧠 AI 性格定制（捏人模式）
使用自然语言或滑块生成 AI 人格特征，并转化为 system prompt

🪞 说话风格克隆（Clone 模式）
通过参考文本分析语气、句式、口头禅，复刻回复风格

💬 流式对话输出
基于 DeepSeek API，前端逐字显示回复

🧾 用户记忆系统（v1）
支持对话历史 + 核心记忆抽取与持久化

🧱 工程化结构
路由拆分、职责清晰，方便后续扩展 OCR、多模型或登录系统

🛠 技术栈

后端：FastAPI

大模型：DeepSeek Chat API

前端：原生 HTML / CSS / JavaScript（内嵌在 FastAPI）

存储：本地 JSON 文件（用户数据、记忆）

运行方式：本地启动（支持 Conda / venv）

📁 项目结构
project/
├── main.py                 # 应用入口（创建 app / 注册 router）
├── run.py                  # 启动脚本
├── config.py               # 全局配置（API Key / 参数 / 进度状态）
├── chat_core.py            # 对话核心逻辑（Prompt 拼接 / DeepSeek 调用）
├── data_store.py           # 用户数据与记忆存储
├── routers/                # 路由模块
│   ├── page.py             # 首页（/）HTML
│   ├── customize.py        # AI 定制 / 克隆 + 进度接口
│   └── chat.py             # 聊天接口（流式）
├── requirements.txt        # pip 依赖
├── environment.yml         # conda 环境（可选）
└── user_data.json          # 本地用户数据（自动生成）
🚀 快速开始
1️⃣ 准备环境
方式一：使用 Conda（推荐）
conda env create -f environment.yml
conda activate virtual-treehole
方式二：使用 venv + pip
python -m venv venv
source venv/bin/activate  # Windows 使用 venv\Scripts\activate
pip install -r requirements.txt
2️⃣ 配置环境变量

在项目根目录创建 .env 文件：

DEEPSEEK_API_KEY=你的_API_KEY
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_API_URL=https://api.deepseek.com/chat/completions
PORT=8000
3️⃣ 启动项目
python run.py

浏览器访问：

http://localhost:8000
🏗 架构设计说明（Architecture）

本项目遵循 “薄路由 + 核心逻辑集中 + 数据最小持久化” 的设计原则，目标是在保持简单的前提下，避免代码失控膨胀。

🧩 核心模块职责划分
1️⃣ main.py —— 应用装配层

只做三件事：

初始化 FastAPI 应用

注册各个 Router

启动服务

❌ 不允许出现：业务逻辑 / Prompt 拼接 / 数据读写

main.py 的目标是 “一眼看完，不需要思考”。

2️⃣ routers/* —— 接口与协议层

每个 router 只负责：

参数校验

请求 / 响应格式

调用核心逻辑

routers/
├── page.py        # 首页 HTML / 静态交互
├── customize.py   # AI 定制 / 克隆 + 进度接口
└── chat.py        # 对话接口（流式输出）

Router 不应关心 Prompt 如何生成、记忆如何存储。

3️⃣ chat_core.py —— 对话核心引擎

这是项目的 中枢神经，负责：

system prompt 构建

history / memory 拼接策略

DeepSeek API 调用

流式响应解析

它的输入是：

当前用户输入

system prompt

历史上下文

记忆数据

输出永远只有一件事：

模型回复（stream / 非 stream）

4️⃣ data_store.py —— 数据与记忆层

负责所有 “活得比一次请求久” 的数据：

用户 system prompt

history 对话记录

memories 核心记忆

当前实现方式：

本地 JSON 文件（user_data.json）

设计目标：

接口稳定

存储实现可替换（JSON → SQLite → Redis）

5️⃣ config.py —— 全局配置与状态

集中管理：

API Key / 模型名

对话参数（max_tokens / temperature）

customize_progress（当前为内存态）

⚠️ customize_progress 是临时方案，未来应替换为可管理的状态模块。

🔁 一次完整对话的调用链
浏览器
  ↓
/chat_stream (router)
  ↓
chat_core.generate_response()
  ↓
- 读取 system prompt
- 拼接 history
- 拼接 memory
  ↓
DeepSeek API
  ↓
流式返回
  ↓
前端逐字渲染
🧠 架构设计原则总结

Router 不做决策

核心逻辑集中，可测试

数据存储最小化，但接口先行

允许简化，但不允许混乱

🧭 使用流程说明
① 定制 AI 性格

输入 user_id

选择模式：

捏人模式：描述性格或使用滑块

克隆模式：粘贴 ≥50 字参考文本

点击「确认定制」

等待进度条完成

定制结果会生成 system prompt 并持久化保存

② 开始聊天

在聊天框输入内容

AI 将基于：

system prompt

用户历史对话

用户核心记忆 进行回复

回复采用 流式输出，实时显示。

🧠 记忆系统说明（Memory v1）

当前版本记忆策略：

history：

保存最近 N 轮完整对话（可配置）

memories：

通过关键词触发（如“我叫…”、“我一直…”）

提取原句摘要

最多保留 5 条核心记忆
