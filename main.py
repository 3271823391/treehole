from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from pydantic import BaseModel
import time
from config import HOST, PORT, customize_progress
from data_store import load_user_data, save_user_data, add_user_memory
from chat_core import (
    extract_personality_for_create, extract_personality_for_clone,
    generate_system_prompt_create, generate_system_prompt_clone,
    stream_chat_with_deepseek
)

app = FastAPI(title="DeepSeek流式虚拟树洞（精细化版）")


# 定义参数模型
class CustomizeRequest(BaseModel):
    user_id: str
    mode: str
    data: str


class ChatStreamRequest(BaseModel):
    user_id: str
    user_input: str


# 前端页面（精细化优化）
@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>树洞 | 你的专属AI倾诉空间</title>
        <!-- 引入Tailwind CSS -->
        <script src="https://cdn.tailwindcss.com"></script>
        <!-- 引入Font Awesome图标 -->
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            /* 全局样式 */
            body {
                font-family: 'Inter', system-ui, -apple-system, sans-serif;
                background: linear-gradient(135deg, #f5f7fa 0%, #e4eaf5 100%);
                min-height: 100vh;
                color: #334155;
            }
            .container {
                max-width: 900px;
                margin: 0 auto;
                padding: 20px 15px;
            }
            /* 卡片样式 */
            .card {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 16px;
                box-shadow: 0 8px 32px rgba(15, 23, 42, 0.08);
                padding: 28px;
                margin-bottom: 24px;
                transition: all 0.3s ease;
            }
            .card:hover {
                box-shadow: 0 12px 40px rgba(15, 23, 42, 0.12);
            }
            /* 标题样式 */
            .section-title {
                font-size: 1.5rem;
                font-weight: 600;
                color: #1e293b;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .section-title i {
                color: #4f46e5;
            }
            /* 输入框样式 */
            .form-input {
                width: 100%;
                padding: 14px 16px;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                font-size: 1rem;
                transition: all 0.2s ease;
                background: #f8fafc;
            }
            .form-input:focus {
                outline: none;
                border-color: #4f46e5;
                box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
                background: #ffffff;
            }
            .form-input::placeholder {
                color: #94a3b8;
            }
            /* 按钮样式 */
            .btn {
                background: #4f46e5;
                color: white;
                border: none;
                border-radius: 12px;
                padding: 12px 24px;
                font-size: 1rem;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s ease;
                display: inline-flex;
                align-items: center;
                gap: 8px;
            }
            .btn:hover {
                background: #4338ca;
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2);
            }
            .btn:active {
                transform: translateY(0);
            }
            .btn:disabled {
                background: #94a3b8;
                cursor: not-allowed;
                transform: none;
                box-shadow: none;
            }
            /* 进度条样式 */
            .progress-container {
                width: 100%;
                height: 8px;
                background: #f1f5f9;
                border-radius: 4px;
                margin: 16px 0;
                display: none;
                overflow: hidden;
                position: relative;
            }
            .progress-bar {
                height: 100%;
                width: 0%;
                background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%);
                border-radius: 4px;
                transition: width 0.2s ease;
            }
            .progress-bar::after {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                height: 100%;
                width: 30%;
                background: rgba(255, 255, 255, 0.2);
                animation: progressShine 1.5s infinite;
            }
            .progress-bar.error {
                background: linear-gradient(90deg, #ef4444 0%, #dc2626 100%);
            }
            .progress-bar.success {
                background: linear-gradient(90deg, #10b981 0%, #059669 100%);
            }
            @keyframes progressShine {
                0% { transform: translateX(-100%); }
                100% { transform: translateX(300%); }
            }
            /* 进度文本 */
            .progress-text {
                font-size: 0.9rem;
                color: #64748b;
                margin-top: 8px;
                display: none;
                display: flex;
                align-items: center;
                gap: 6px;
            }
            /* 提示文本 */
            .mode-tip {
                font-size: 0.9rem;
                color: #64748b;
                margin: -8px 0 16px 0;
                line-height: 1.5;
            }
            .clone-tip {
                color: #f97316;
                font-weight: 500;
                font-size: 0.9rem;
                margin: 8px 0;
                padding: 8px 12px;
                background: rgba(249, 115, 22, 0.05);
                border-radius: 8px;
                display: none;
            }
            /* 结果提示 */
            .result {
                margin-top: 16px;
                padding: 12px 16px;
                border-radius: 8px;
                font-size: 0.95rem;
                line-height: 1.5;
            }
            .result.success {
                background: rgba(16, 185, 129, 0.08);
                color: #059669;
            }
            .result.error {
                background: rgba(239, 68, 68, 0.08);
                color: #dc2626;
            }
            /* 聊天记录样式 */
            .chat-history {
                margin-top: 16px;
                height: 400px;
                overflow-y: auto;
                padding: 16px;
                border-radius: 12px;
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                scrollbar-width: thin;
                scrollbar-color: #cbd5e1 #f8fafc;
            }
            .chat-history::-webkit-scrollbar {
                width: 6px;
            }
            .chat-history::-webkit-scrollbar-track {
                background: #f8fafc;
                border-radius: 3px;
            }
            .chat-history::-webkit-scrollbar-thumb {
                background: #cbd5e1;
                border-radius: 3px;
            }
            .chat-history::-webkit-scrollbar-thumb:hover {
                background: #94a3b8;
            }
            .chat-message {
                margin-bottom: 16px;
                max-width: 80%;
                line-height: 1.6;
            }
            .chat-message.user {
                margin-left: auto;
            }
            .chat-message.ai {
                margin-right: auto;
            }
            .chat-bubble {
                padding: 12px 16px;
                border-radius: 18px;
                position: relative;
            }
            .user .chat-bubble {
                background: #4f46e5;
                color: white;
                border-bottom-right-radius: 4px;
            }
            .ai .chat-bubble {
                background: white;
                color: #334155;
                border: 1px solid #e2e8f0;
                border-bottom-left-radius: 4px;
            }
            .chat-avatar {
                width: 36px;
                height: 36px;
                border-radius: 50%;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                font-size: 0.8rem;
                font-weight: 600;
                margin-bottom: 4px;
            }
            .user .chat-avatar {
                background: #4338ca;
                color: white;
                margin-left: auto;
            }
            .ai .chat-avatar {
                background: #e0e7ff;
                color: #4f46e5;
            }
            /* 打字动画 */
            .typing::after {
                content: '';
                display: inline-block;
                width: 18px;
                height: 18px;
                margin-left: 8px;
                border-radius: 50%;
                background: #94a3b8;
                animation: typing 1.4s infinite ease-in-out both;
            }
            .typing::before {
                content: '';
                display: inline-block;
                width: 18px;
                height: 18px;
                margin-left: 4px;
                border-radius: 50%;
                background: #94a3b8;
                animation: typing 1.4s infinite ease-in-out both;
                animation-delay: -0.32s;
            }
            .typing span::after {
                content: '';
                display: inline-block;
                width: 18px;
                height: 18px;
                margin-left: 4px;
                border-radius: 50%;
                background: #94a3b8;
                animation: typing 1.4s infinite ease-in-out both;
                animation-delay: -0.64s;
            }
            @keyframes typing {
                0%, 80%, 100% { transform: scale(0); }
                40% { transform: scale(1); }
            }
            /* 下拉框样式 */
            .select-wrapper {
                position: relative;
                margin: 16px 0;
            }
            .form-select {
                width: 100%;
                padding: 14px 16px;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                font-size: 1rem;
                background: #f8fafc url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' fill='%2394a3b8' viewBox='0 0 16 16'%3E%3Cpath d='M8 11l4-4H4l4 4z'/%3E%3C/svg%3E") right 16px center no-repeat;
                appearance: none;
                transition: all 0.2s ease;
            }
            .form-select:focus {
                outline: none;
                border-color: #4f46e5;
                box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
                background-color: #ffffff;
                background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' fill='%234f46e5' viewBox='0 0 16 16'%3E%3Cpath d='M8 11l4-4H4l4 4z'/%3E%3C/svg%3E");
            }
            /* 响应式调整 */
            @media (max-width: 768px) {
                .card {
                    padding: 20px;
                }
                .section-title {
                    font-size: 1.3rem;
                }
                .chat-history {
                    height: 300px;
                }
                .btn {
                    width: 100%;
                    justify-content: center;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <!-- 头部标题 -->
            <header class="text-center mb-10">
                <h1 class="text-3xl font-bold text-[#1e293b] mb-2">
                    <<i class="fa-solid fa-tree"></</i> 树洞
                </h1>
                <p class="text-[#64748b] text-lg">你的专属AI倾诉空间，想说就说，安心陪伴</p>
            </header>

            <!-- 定制AI性格卡片 -->
            <div class="card">
                <h2 class="section-title">
                    <<i class="fa-solid fa-user-gear"></</i> 定制你的AI陪伴
                </h2>
                <input 
                    type="text" 
                    id="user_id" 
                    class="form-input" 
                    placeholder="输入你的专属ID（如：summer081）" 
                    required
                >
                <div class="select-wrapper">
                    <select id="custom_mode" class="form-select" onchange="changeModeTip()">
                        <option value="捏人">捏人模式（自定义性格）</option>
                        <option value="clone">克隆模式（复刻参考风格）</option>
                    </select>
                </div>
                <div id="mode_tip" class="mode-tip">
                    捏人模式：描述AI性格（例：温柔度90，毒舌度10，共情方式是倾听和鼓励，口头禅"没关系呀"）
                </div>
                <textarea 
                    id="custom_data" 
                    class="form-input" 
                    placeholder="捏人模式示例：温柔度90，毒舌度10，共情方式是倾听和鼓励，回复用中句，口头禅是没关系呀，语气软糯" 
                    rows="5"
                ></textarea>
                <div id="clone_warning" class="clone-tip">
                    <<i class="fa-solid fa-lightbulb"></</i> 克隆模式要求：参考文本≥50字（可粘贴聊天记录/语气示例，AI将100%复刻）
                </div>
                <button onclick="customizeCharacter()" class="btn">
                    <<i class="fa-solid fa-wand-magic-sparkles"></</i> 确认定制
                </button>
                <div id="custom_progress" class="progress-container">
                    <div id="progress_bar" class="progress-bar"></div>
                </div>
                <div id="progress_text" class="progress-text">
                    <<i class="fa-solid fa-circle-notch fa-spin"></</i> 进度：0%（初始化）
                </div>
                <div id="custom_result" class="result"></div>
            </div>

            <!-- 聊天区域卡片 -->
            <div class="card">
                <h2 class="section-title">
                    <<i class="fa-solid fa-comments"></</i> 开始倾诉（逐字生成）
                </h2>
                <textarea 
                    id="chat_input" 
                    class="form-input" 
                    placeholder="在这里输入你想倾诉的话...（如：今天工作好累，感觉压力好大）" 
                    rows="4"
                ></textarea>
                <button onclick="sendStreamChat()" class="btn">
                    <<i class="fa-solid fa-paper-plane"></</i> 发送消息
                </button>
                <div id="chat_history" class="chat-history"></div>
            </div>

            <!-- 页脚 -->
            <footer class="text-center text-[#94a3b8] text-sm mt-8 pb-10">
                <p>© 2025 树洞 | 安全加密 · 隐私保护 · 仅用于倾诉交流</p>
                <p class="mt-2">心理援助热线：12320（全国） | 400-161-9995（24小时）</p>
            </footer>
        </div>

        <script>
            let progressTimer = null;

            // 切换模式提示
            function changeModeTip() {
                const mode = document.getElementById("custom_mode").value;
                const modeTip = document.getElementById("mode_tip");
                const customData = document.getElementById("custom_data");
                const cloneWarning = document.getElementById("clone_warning");

                if (mode === "clone") {
                    modeTip.innerText = "克隆模式：粘贴参考文本（聊天记录/语气示例），AI将完全复刻说话风格、口头禅和表达方式";
                    customData.placeholder = "克隆模式示例：\\n用户：今天好累啊\\n好友：累了就歇会儿呗～多大点事儿，反正慢慢来嘛，总会好的😜\\n用户：感觉啥都做不好\\n好友：别瞎想啦！你已经很棒了，我一直都在的～有我陪着你呢！";
                    cloneWarning.style.display = "block";
                } else {
                    modeTip.innerText = "捏人模式：描述AI性格（例：温柔度90，毒舌度10，共情方式是倾听和鼓励，口头禅\"没关系呀\"）";
                    customData.placeholder = "捏人模式示例：温柔度90，毒舌度10，共情方式是倾听和鼓励，回复用中句，口头禅是没关系呀，语气软糯，喜欢用表情符号";
                    cloneWarning.style.display = "none";
                }
            }

            // 进度文本映射
            function getProgressText(percent, mode) {
                const textMap = {
                    0: "进度：0%（初始化）",
                    10: "进度：10%（参数校验中）",
                    20: "进度：20%（准备分析数据）",
                    30: "进度：30%（数据预处理完成）",
                    40: mode === "clone" ? "进度：40%（分析参考文本风格）" : "进度：40%（提取性格特征）",
                    45: mode === "clone" ? "进度：45%（提取核心风格特征）" : "进度：45%（提取核心性格特征）",
                    50: mode === "clone" ? "进度：50%（调用AI分析风格）" : "进度：50%（调用AI分析性格）",
                    55: mode === "clone" ? "进度：55%（AI风格分析完成）" : "进度：55%（AI性格分析完成）",
                    60: mode === "clone" ? "进度：60%（风格特征提取完成）" : "进度：60%（性格特征提取完成）",
                    70: mode === "clone" ? "进度：70%（生成复刻风格Prompt）" : "进度：70%（生成定制Prompt）",
                    75: mode === "clone" ? "进度：75%（优化复刻Prompt）" : "进度：75%（优化定制Prompt）",
                    80: mode === "clone" ? "进度：80%（调用AI生成Prompt）" : "进度：80%（调用AI生成Prompt）",
                    85: mode === "clone" ? "进度：85%（AI Prompt生成完成）" : "进度：85%（AI Prompt生成完成）",
                    90: mode === "clone" ? "进度：90%（复刻Prompt生成完成）" : "进度：90%（定制Prompt生成完成）",
                    95: "进度：95%（准备保存数据）",
                    100: mode === "clone" ? "进度：100%（风格复刻完成）" : "进度：100%（性格定制完成）",
                    "-1": "进度：失败（处理出错）"
                };
                return textMap[percent] || `进度：${percent}%（处理中）`;
            }

            // 轮询进度
            function pollProgress(user_id, mode) {
                const progressBar = document.getElementById("progress_bar");
                const progressText = document.getElementById("progress_text");

                progressBar.style.width = "0%";
                progressText.innerHTML = `<<i class="fa-solid fa-circle-notch fa-spin"></</i> ${getProgressText(0, mode)}`;

                progressTimer = setInterval(async () => {
                    try {
                        const resp = await fetch(`/get_customize_progress?user_id=${user_id}`);
                        const res = await resp.json();
                        const percent = res.progress;

                        progressBar.style.width = `${Math.max(0, percent)}%`;
                        progressText.innerHTML = `<<i class="fa-solid fa-circle-notch fa-spin"></</i> ${getProgressText(percent, mode)}`;

                        if (percent === 100 || percent === -1) {
                            clearInterval(progressTimer);
                            progressBar.classList.add(percent === 100 ? "success" : "error");
                            progressText.innerHTML = percent === 100 
                                ? `<<i class="fa-solid fa-check-circle"></</i> ${getProgressText(percent, mode)}`
                                : `<<i class="fa-solid fa-exclamation-circle"></</i> ${getProgressText(percent, mode)}`;
                        }
                    } catch (e) {
                        clearInterval(progressTimer);
                        progressText.innerHTML = `<<i class="fa-solid fa-exclamation-circle"></</i> 进度：查询失败`;
                    }
                }, 50);
            }

            // 定制性格函数
            async function customizeCharacter() {
                const user_id = document.getElementById("user_id").value.trim();
                const mode = document.getElementById("custom_mode").value;
                const data = document.getElementById("custom_data").value.trim();
                const resultDom = document.getElementById("custom_result");
                const progressContainer = document.getElementById("custom_progress");
                const progressBar = document.getElementById("progress_bar");
                const progressText = document.getElementById("progress_text");
                const btn = document.querySelector(".btn");

                // 重置状态
                resultDom.className = "result";
                resultDom.innerText = "";
                progressBar.className = "progress-bar";
                progressContainer.style.display = "block";
                progressText.style.display = "block";
                btn.disabled = true;
                btn.innerHTML = `<<i class="fa-solid fa-spinner fa-spin"></</i> 处理中...`;

                if (progressTimer) clearInterval(progressTimer);

                // 基础校验
                if (!user_id) {
                    progressContainer.style.display = "none";
                    progressText.style.display = "none";
                    resultDom.className = "result error";
                    resultDom.innerText = "❌ 错误：用户ID不能为空，请输入专属标识";
                    btn.disabled = false;
                    btn.innerHTML = `<<i class="fa-solid fa-wand-magic-sparkles"></</i> 确认定制`;
                    return;
                }

                if (!data) {
                    progressContainer.style.display = "none";
                    progressText.style.display = "none";
                    resultDom.className = "result error";
                    resultDom.innerText = `❌ 错误：请输入${mode === "clone" ? "参考文本" : "性格描述"}`;
                    btn.disabled = false;
                    btn.innerHTML = `<<i class="fa-solid fa-wand-magic-sparkles"></</i> 确认定制`;
                    return;
                }

                if (mode === "clone" && data.length < 50) {
                    progressContainer.style.display = "none";
                    progressText.style.display = "none";
                    resultDom.className = "result error";
                    resultDom.innerText = "❌ 错误：克隆模式参考文本长度需≥50字，请补充完整";
                    btn.disabled = false;
                    btn.innerHTML = `<<i class="fa-solid fa-wand-magic-sparkles"></</i> 确认定制`;
                    return;
                }

                try {
                    // 初始化进度
                    await fetch(`/set_progress?user_id=${user_id}&progress=0`);
                    // 启动轮询
                    pollProgress(user_id, mode);
                    // 延迟发起请求
                    await new Promise(resolve => setTimeout(resolve, 300));

                    const resp = await fetch("/customize", {
                        method: "POST",
                        headers: {"Content-Type": "application/json"},
                        body: JSON.stringify({user_id, mode, data})
                    });

                    const res = await resp.json();
                    if (res.success) {
                        resultDom.className = "result success";
                        resultDom.innerText = `✅ ${res.message}`;
                    } else {
                        resultDom.className = "result error";
                        resultDom.innerText = `❌ 定制失败：${res.message || "未知错误"}`;
                        progressBar.classList.add("error");
                    }

                    // 恢复按钮状态
                    setTimeout(() => {
                        btn.disabled = false;
                        btn.innerHTML = `<<i class="fa-solid fa-wand-magic-sparkles"></</i> 确认定制`;
                        // 隐藏进度条
                        setTimeout(() => {
                            progressContainer.style.display = "none";
                            progressText.style.display = "none";
                        }, 2000);
                    }, 1000);

                } catch (e) {
                    if (progressTimer) clearInterval(progressTimer);
                    progressBar.classList.add("error");
                    progressText.innerHTML = `<<i class="fa-solid fa-exclamation-circle"></</i> 进度：失败（${e.message}）`;
                    resultDom.className = "result error";
                    resultDom.innerText = `❌ 请求失败：${e.message}`;

                    // 恢复按钮状态
                    setTimeout(() => {
                        btn.disabled = false;
                        btn.innerHTML = `<<i class="fa-solid fa-wand-magic-sparkles"></</i> 确认定制`;
                    }, 1000);
                }
            }

            // 流式聊天函数
            async function sendStreamChat() {
                const user_id = document.getElementById("user_id").value.trim();
                const input = document.getElementById("chat_input").value.trim();
                const historyDom = document.getElementById("chat_history");
                const btn = document.querySelectorAll(".btn")[1];

                if (!user_id) {
                    alert("请先输入用户ID并完成AI性格定制～");
                    return;
                }

                if (!input) {
                    alert("请输入想倾诉的内容呀～");
                    return;
                }

                // 添加用户消息到聊天记录
                const userMsgHtml = `
                    <div class="chat-message user">
                        <div class="chat-avatar">我</div>
                        <div class="chat-bubble">${input}</div>
                    </div>
                `;
                historyDom.innerHTML += userMsgHtml;
                document.getElementById("chat_input").value = "";
                historyDom.scrollTop = historyDom.scrollHeight;

                // 显示AI正在输入
                const aiReplyId = "ai_reply_" + Date.now();
                const aiLoadingHtml = `
                    <div class="chat-message ai">
                        <div class="chat-avatar">AI</div>
                        <div class="chat-bubble typing"><span></span></div>
                    </div>
                `;
                historyDom.innerHTML += aiLoadingHtml;
                historyDom.scrollTop = historyDom.scrollHeight;
                btn.disabled = true;
                btn.innerHTML = `<<i class="fa-solid fa-spinner fa-spin"></</i> 发送中...`;

                try {
                    const resp = await fetch("/chat_stream", {
                        method: "POST",
                        headers: {"Content-Type": "application/json"},
                        body: JSON.stringify({user_id, user_input: input})
                    });

                    if (!resp.ok) throw new Error(`请求失败：${resp.status}`);

                    const reader = resp.body.getReader();
                    const decoder = new TextDecoder();
                    let aiReply = "";
                    const aiReplyDom = document.querySelector(`#${aiReplyId} .chat-bubble`);

                    // 移除打字动画
                    aiReplyDom.classList.remove("typing");
                    aiReplyDom.innerHTML = "";

                    while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;

                        const char = decoder.decode(value, { stream: true });
                        aiReply += char;
                        aiReplyDom.innerText = aiReply;
                        historyDom.scrollTop = historyDom.scrollHeight;
                    }

                    // 如果没有回复内容
                    if (!aiReply) {
                        aiReplyDom.innerText = "抱歉～暂时无法回复，请稍后再试呀～";
                    }

                } catch (e) {
                    const aiReplyDom = document.querySelector(`#${aiReplyId} .chat-bubble`);
                    aiReplyDom.classList.remove("typing");
                    aiReplyDom.innerText = `😥 请求失败：${e.message}`;
                } finally {
                    // 恢复按钮状态
                    btn.disabled = false;
                    btn.innerHTML = `<<i class="fa-solid fa-paper-plane"></</i> 发送消息`;
                }
            }

            // 输入框回车提交
            document.getElementById("chat_input").addEventListener("keydown", (e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    sendStreamChat();
                }
            });
        </script>
    </body>
    </html>
    """


# 进度接口（不变）
@app.get("/set_progress")
async def set_progress(user_id: str, progress: int):
    customize_progress[user_id] = progress
    return JSONResponse({"success": True})


@app.get("/get_customize_progress")
async def get_customize_progress(user_id: str):
    return JSONResponse({
        "progress": customize_progress.get(user_id, 0)
    })


# 定制接口（不变）
@app.post("/customize")
async def customize_character(req: CustomizeRequest):
    user_id = req.user_id.strip()
    mode = req.mode.strip()
    data = req.data.strip()
    user_info = load_user_data(user_id)
    try:
        customize_progress[user_id] = 10
        time.sleep(0.3)
        customize_progress[user_id] = 20
        time.sleep(0.3)
        customize_progress[user_id] = 30
        time.sleep(0.3)

        if mode == "clone":
            personality = extract_personality_for_clone(data, user_id)
            system_prompt = generate_system_prompt_clone(personality, user_id)
        else:
            personality = extract_personality_for_create(data, user_id)
            system_prompt = generate_system_prompt_create(personality, user_id)

        customize_progress[user_id] = 90
        time.sleep(0.3)
        customize_progress[user_id] = 95
        time.sleep(0.3)
        customize_progress[user_id] = 100

        user_info["system_prompt"] = system_prompt
        save_user_data(user_id, user_info)
        success_msg = "性格定制成功！可以开始流式聊天了" if mode != "clone" else "风格复刻成功！AI将完全模仿参考文本的说话风格"
        return JSONResponse({"success": True, "message": success_msg})
    except Exception as e:
        customize_progress[user_id] = -1
        import traceback
        return JSONResponse({
            "success": False,
            "message": f"定制失败：{str(e)}",
            "detail": traceback.format_exc()
        }, status_code=500)


# 流式聊天接口（不变）
@app.post("/chat_stream")
async def chat_stream(req: ChatStreamRequest):
    user_id = req.user_id.strip()
    user_input = req.user_input.strip()
    user_info = load_user_data(user_id)

    if not user_info["system_prompt"]:
        raise HTTPException(status_code=400, detail="请先完成AI性格定制后再聊天")

    if len(user_input) > 20:
        add_user_memory(user_id, user_input)

    return StreamingResponse(
        stream_chat_with_deepseek(user_id, user_input, user_info["system_prompt"], user_info["history"]),
        media_type="text/plain"
    )


# 启动函数（不变）
def run_api():
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
