# AI 树洞（FastAPI）

## 项目简介

AI 树洞是一个面向心理倾诉与情绪陪伴场景的轻量型对话应用，强调“可持续演进的产品结构”和“清晰的工程边界”。它基于 FastAPI 提供服务，前端为原生 HTML/CSS/JavaScript，支持流式对话、用户中心与基础记忆持久化。

## 多设备 UI 适配说明

- **桌面端 / 平板端**：采用主聊天区 + 右侧信息栏布局。右侧包含用户身份卡片与情绪分析报告，便于并行查看资料与情绪状态。
- **移动端**：隐藏右侧栏，将用户身份与情绪分析入口收敛至顶部蓝色区域的两个按钮。点击按钮后以弹窗形式查看用户信息或情绪报告，保证聊天区拥有更完整的可视空间。

## 版本差异（Free / Plus / Pro）

- **Free**：轻量匿名体验，适合快速试用或公开演示。
- **Plus**：基于可持久化身份的增强体验（头像/用户名/情绪报告）。
- **Pro**：在 Plus 的基础上提供语音克隆与语音输出配置入口。

> 页面入口示例：`/treehole_free.html`、`/treehole_plus.html`、`/treehole_pro.html`（以路由配置为准）。

## 用户身份与记忆机制

- **用户名即身份标识**：系统以用户名派生用户标识。
  - 规则：`user_id = "u_" + sha1(username.trim().toLowerCase())`
- **用户名与聊天记忆绑定**：所有对话历史与记忆均与 `user_id` 关联。
- **修改用户名会切换到新的对话记忆**：因为 `user_id` 发生变化，会进入另一套全新的对话历史。
- **本地缓存**：浏览器使用 `localStorage` 保存 `last_username`，刷新后可恢复上一次使用的用户名。

## 用户身份与资料功能

- **自定义用户名**：作为用户身份标识，影响 `user_id` 与对话记忆归属。
- **自定义头像**：上传后即刻更新头像展示，并绑定到当前用户档案。
- **跨刷新/跨设备恢复**：只要使用相同用户名，即可恢复该身份下的历史记录与头像。

## 交互设计说明

- **用户名自动保存**：在输入框失焦或停止输入后自动调用 `/profile` 保存，并立即切换到新的 `user_id`。
- **头像自动上传**：选择图片后立即上传到 `/avatar_upload`，成功后同步更新用户头像。
- **移动端无侧栏**：为保证主要聊天区域的可视高度与可读性，移动端以弹窗式入口承载用户资料与情绪报告。

## 头像与数据存储

- 头像文件存储在：`static/avatars`。
- 用户档案与对话数据存储在本地 JSON 文件（`user_data.json`）。
- 当前版本为**无账号系统**方案，不包含 PIN 或注册流程。

## Pro：语音克隆使用方式

1. 打开 Pro 页面右侧卡片或移动端底部入口，进入「语音克隆」面板。
2. 填写 `voice_profile_id`（3~32 位字母/数字/下划线），这是自定义语音的唯一标识，会被持久化到 `localStorage`。
3. 上传参考音频后，后端会返回第三方的 `audioId`，同时将其绑定到 `user_id`（保存到 `user_data.json`）：
   ```json
   {
     "voice": {
       "profile_id": "your_profile_id",
       "audioId": "returned_audio_id"
     }
   }
   ```
4. 语音输出会读取这份映射作为克隆音色来源，因此未绑定 `audioId` 时无法合成克隆音色。

## Pro：语音输出（LipVoice 克隆 TTS）

- 位置：Pro 页面右侧菜单（移动端抽屉）里的「语音输出」滑块。
- 原理：AI 流式文本输出时按句子切分，依次调用 `/api/voice_clone/tts` 合成音频并播放。
- 特点：直接播放音频流，不生成文件也不触发下载；会使用上传后保存的 `audioId` 音色。
- iOS Safari 注意事项：
  - 首次播放需要用户手势解锁（发送按钮点击会自动尝试解锁）。
  - 若静音模式/音量过低，会导致听不到声音。
  - 若仍无声，请检查浏览器是否允许音频播放权限。

## Render 环境变量（LipVoice）

Render 环境变量示例（后端使用）：

```bash
LIPVOICE_SIGN=你的签名                # 必填
LIPVOICE_BASE_URL=https://openapi.lipvoice.cn  # 可选，默认使用官方地址
```

> 安全提醒：`LIPVOICE_SIGN` 只能配置在服务端环境变量中，绝不能出现在前端。

## 常见故障排查

1. **仍是机械音（或默认音色）？**  
   - 检查是否调用 `/api/voice_clone/tts`（浏览器 Network 面板应看到请求）。  
   - 确认 `user_data.json` 中当前用户已保存 `voice.audioId`。  
   - 确认后端请求 LipVoice 时携带 `audioId`（否则会回落默认音色）。
2. **语音输出无声？**  
   - 确认语音输出开关已开启。  
   - iOS Safari 需要用户手势解锁（点击发送按钮）。  
   - 确认系统未静音、音量正常、浏览器允许播放声音。  
3. **footer 仍会随滚动移动？**  
   - 确认版权条不在任何滚动容器内（必须在 `#appShell` 外）。  
   - 检查父级是否有 `transform`，会改变 `position: fixed` 的定位参考。  
   - 确认页面滚动发生在 `#mainScroll`，而不是 `body/html`。

## 常见问题（FAQ）

1. **iPhone 键盘弹出导致布局抖动？**  
   Pro 页面采用固定 App Shell + 内部滚动容器方案，避免 `body` 滚动和 footer 被键盘推起。
2. **没有声音？**  
   - 检查语音输出开关是否开启。
   - 确认浏览器允许声音播放、系统音量正常。
   - iOS Safari 需要用户手势解锁（点一次页面/发送按钮即可）。
   - 如果浏览器没有可用的语音引擎，会无法播报。

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
