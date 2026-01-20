from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>树洞 - 你的AI倾诉空间</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

            body {
                font-family: 'Inter', system-ui, -apple-system, sans-serif;
                background: linear-gradient(135deg, #f0f4f8 0%, #e6eef7 100%);
                color: #334155;
                min-height: 100vh;
                margin: 0;
                padding: 20px 0;
                line-height: 1.6;
            }

            .container {
                max-width: 850px;
                margin: 0 auto;
                padding: 0 20px;
            }

            .card {
                background: white;
                border-radius: 16px;
                padding: 28px;
                margin-bottom: 24px;
                border: 1px solid #e2e8f0;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            }

            .card:hover {
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.07), 0 4px 6px -2px rgba(0, 0, 0, 0.04);
            }

            .section-title {
                font-size: 1.25rem;
                font-weight: 600;
                color: #1e293b;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                gap: 10px;
                letter-spacing: -0.01em;
            }

            .section-title i {
                color: #3b82f6;
                font-size: 1.1em;
            }

            .form-input {
                width: 100%;
                padding: 14px 16px;
                border: 1px solid #cbd5e1;
                border-radius: 10px;
                font-size: 1rem;
                margin-bottom: 16px;
                box-sizing: border-box;
                background: #f8fafc;
                transition: all 0.2s ease;
                color: #1e293b;
            }

            .form-input:focus {
                outline: none;
                border-color: #3b82f6;
                background: white;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
            }

            .form-input::placeholder {
                color: #94a3b8;
            }

            .btn {
                background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 14px 24px;
                font-size: 1rem;
                font-weight: 500;
                cursor: pointer;
                display: inline-flex;
                align-items: center;
                gap: 10px;
                transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
                box-shadow: 0 4px 6px rgba(59, 130, 246, 0.2);
                position: relative;
                overflow: hidden;
            }

            .btn:hover {
                transform: translateY(-1px);
                box-shadow: 0 6px 12px rgba(59, 130, 246, 0.25);
            }

            .btn:active {
                transform: translateY(0);
                box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
            }

            .btn:disabled {
                background: #cbd5e1;
                cursor: not-allowed;
                transform: none;
                box-shadow: none;
            }

            .btn i {
                font-size: 1.1em;
            }

            /* 进度条容器 */
            .progress-container {
                margin: 24px 0;
                opacity: 0;
                transform: translateY(10px);
                transition: all 0.4s ease;
            }

            .progress-container.show {
                opacity: 1;
                transform: translateY(0);
            }

            /* 进度条样式 */
            .progress-bar-wrapper {
                background: #e2e8f0;
                border-radius: 12px;
                overflow: hidden;
                height: 10px;
                position: relative;
                box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.05);
            }

            .progress-bar-fill {
                height: 100%;
                background: linear-gradient(90deg, #3b82f6 0%, #60a5fa 100%);
                border-radius: 12px;
                width: 0%;
                transition: width 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
                position: relative;
            }

            .progress-bar-fill::after {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: linear-gradient(
                    90deg,
                    transparent,
                    rgba(255, 255, 255, 0.3),
                    transparent
                );
                animation: shimmer 1.5s infinite;
            }

            @keyframes shimmer {
                0% { transform: translateX(-100%); }
                100% { transform: translateX(100%); }
            }

            /* 进度文本 */
            .progress-text {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: 12px;
                font-size: 0.875rem;
                color: #64748b;
                font-weight: 500;
            }

            .progress-step {
                display: flex;
                align-items: center;
                gap: 6px;
            }

            .progress-step i {
                font-size: 0.9em;
                opacity: 0.8;
            }

            /* 状态提示 */
            .status-tip {
                font-size: 0.875rem;
                color: #64748b;
                margin: -12px 0 16px 0;
                display: flex;
                align-items: start;
                gap: 8px;
                padding: 10px;
                background: #f1f5f9;
                border-radius: 8px;
                border-left: 4px solid #3b82f6;
            }

            .clone-tip {
                color: #f59e0b;
                background: #fffbeb;
                border-left-color: #f59e0b;
                padding: 10px;
                border-radius: 8px;
                margin: 8px 0 16px 0;
                display: none;
                font-size: 0.875rem;
                align-items: center;
                gap: 8px;
            }

            /* 结果提示 */
            .result {
                padding: 16px;
                border-radius: 10px;
                font-size: 0.875rem;
                margin-top: 16px;
                display: none;
                animation: fadeIn 0.3s ease;
                backdrop-filter: blur(4px);
            }

            .result.show {
                display: block;
            }

            .result.success {
                background: #f0fdf4;
                color: #166534;
                border: 1px solid #bbf7d0;
            }

            .result.error {
                background: #fef2f2;
                color: #dc2626;
                border: 1px solid #fecaca;
            }

            .result i {
                margin-right: 8px;
            }

            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(-5px); }
                to { opacity: 1; transform: translateY(0); }
            }

            /* 聊天区域 */
            .chat-history {
                height: 400px;
                overflow-y: auto;
                padding: 16px;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                margin-top: 20px;
                background: #f8fafc;
                scroll-behavior: smooth;
                box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.03);
            }

            .chat-history::-webkit-scrollbar {
                width: 8px;
            }

            .chat-history::-webkit-scrollbar-track {
                background: #f1f5f9;
                border-radius: 4px;
            }

            .chat-history::-webkit-scrollbar-thumb {
                background: #cbd5e1;
                border-radius: 4px;
            }

            .chat-history::-webkit-scrollbar-thumb:hover {
                background: #94a3b8;
            }

            .chat-msg {
                margin-bottom: 20px;
                max-width: 80%;
                line-height: 1.5;
                animation: messageAppear 0.3s ease;
            }

            @keyframes messageAppear {
                from { opacity: 0; transform: scale(0.95) translateY(5px); }
                to { opacity: 1; transform: scale(1) translateY(0); }
            }

            .chat-msg.user {
                margin-left: auto;
            }

            .chat-msg.ai {
                margin-right: auto;
            }

            .chat-bubble {
                padding: 12px 16px;
                border-radius: 12px;
                font-size: 0.95rem;
                word-wrap: break-word;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            }

            .user .chat-bubble {
                background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
                color: white;
                border-bottom-right-radius: 4px;
            }

            .ai .chat-bubble {
                background: white;
                color: #334155;
                border: 1px solid #e2e8f0;
                border-bottom-left-radius: 4px;
            }

            .chat-loading {
                color: #64748b;
                font-size: 0.875rem;
                padding: 12px 16px;
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .chat-loading i {
                animation: pulse 1.5s infinite;
            }

            @keyframes pulse {
                0%, 100% { opacity: 0.6; }
                50% { opacity: 1; }
            }

            /* 头部样式 */
            header {
                text-align: center;
                margin-bottom: 32px;
                padding: 20px 0;
            }

            header h1 {
                font-size: 2.5rem;
                font-weight: 700;
                color: #1e293b;
                margin-bottom: 8px;
                letter-spacing: -0.02em;
            }

            header p {
                color: #64748b;
                font-size: 1.1rem;
                font-weight: 400;
            }

            /* 页脚 */
            footer {
                text-align: center;
                font-size: 0.875rem;
                color: #64748b;
                margin-top: 40px;
                padding: 16px 0;
                opacity: 0.8;
            }

            /* 响应式优化 */
            @media (max-width: 640px) {
                .container {
                    padding: 0 12px;
                }
                .card {
                    padding: 20px;
                    border-radius: 12px;
                }
                header h1 {
                    font-size: 2rem;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1><i class="fa-solid fa-tree text-3xl mr-3 text-slate-800"></i>树洞</h1>
                <p>安心倾诉，AI陪你聊天</p>
            </header>

            <div class="card">
                <h2 class="section-title">
                    <i class="fa-solid fa-user-pen"></i> 定制AI性格
                </h2>
                <input 
                    type="text" 
                    id="user_id" 
                    class="form-input" 
                    placeholder="输入你的用户ID（如：test001）" 
                    required
                >
                <select id="custom_mode" class="form-input" onchange="switchMode()">
                    <option value="捏人">捏人模式（自定义性格）</option>
                    <option value="clone">克隆模式（复刻参考风格）</option>
                </select>
                <div id="mode_tip" class="status-tip">
                    <i class="fa-solid fa-lightbulb"></i>
                    <span>示例：温柔度90，毒舌度10，共情方式是倾听鼓励</span>
                </div>
                <div id="clone_warning" class="clone-tip">
                    <i class="fa-solid fa-info-circle"></i>
                    克隆模式：参考文本需≥50字（可粘贴聊天记录）
                </div>
                <!-- 性格预设方案（仅捏人模式） -->
                <div id="preset_box" style="
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                margin-bottom: 16px;
            ">
                <button type="button" class="btn" onclick="applyPreset('gentle')">
                    🌸 温柔治愈
                </button>
                <button type="button" class="btn" onclick="applyPreset('rational')">
                    🧠 理性分析
                </button>
                <button type="button" class="btn" onclick="applyPreset('tsundere')">
                    😈 轻毒舌
                </button>
                <button type="button" class="btn" onclick="applyPreset('friend')">
                    🤝 好朋友
                </button>
                <button type="button" class="btn" onclick="applyPreset('listener')">
                    🧘 倾听者
                </button>
            </div>
            <!-- 滑块捏人 -->
            <div id="slider_box" style="margin-bottom: 16px;">
                <div class="status-tip">
                    <i class="fa-solid fa-sliders"></i>
                    <span>拖动滑块，自动生成性格描述</span>
                </div>

                <div style="display: grid; gap: 12px;">
                    <div>
                        <label>🌸 温柔度：<span id="val_gentle">50</span></label>
                        <input type="range" min="0" max="100" value="50" id="gentle"
                               class="w-full" oninput="updatePersonality()">
                    </div>

                    <div>
                        <label>🧠 理性度：<span id="val_rational">50</span></label>
                        <input type="range" min="0" max="100" value="50" id="rational"
                               class="w-full" oninput="updatePersonality()">
                    </div>

                    <div>
                        <label>🤝 陪伴感：<span id="val_companion">50</span></label>
                        <input type="range" min="0" max="100" value="50" id="companion"
                               class="w-full" oninput="updatePersonality()">
                    </div>

                    <div>
                        <label>😈 毒舌度：<span id="val_tsundere">10</span></label>
                        <input type="range" min="0" max="100" value="10" id="tsundere"
                               class="w-full" oninput="updatePersonality()">
                    </div>
                </div>
            </div>
                <textarea 
                    id="custom_data" 
                    class="form-input" 
                    rows="4"
                    placeholder="请输入性格描述或参考文本"
                ></textarea>
                <button onclick="customizeAI()" class="btn" id="custom_btn">
                    <i class="fa-solid fa-check"></i> 确认定制
                </button>

                <div id="progress_container" class="progress-container">
                    <div class="progress-bar-wrapper">
                        <div id="progress_bar_fill" class="progress-bar-fill"></div>
                    </div>
                    <div class="progress-text">
                        <span id="progress_label">进度：0%</span>
                        <span id="progress_step" class="progress-step">
                            <i class="fa-solid fa-circle-notch fa-spin"></i>
                            <span>初始化...</span>
                        </span>
                    </div>
                </div>

                <div id="custom_result" class="result"></div>
            </div>

            <div class="card">
                <h2 class="section-title">
                    <i class="fa-solid fa-comments"></i> 开始聊天
                </h2>
                <textarea 
                    id="chat_input" 
                    class="form-input" 
                    rows="3"
                    placeholder="输入想倾诉的话..."
                ></textarea>
                <button onclick="sendChat()" class="btn" id="chat_btn">
                    <i class="fa-solid fa-paper-plane"></i> 发送
                </button>
                <div id="chat_history" class="chat-history"></div>
            </div>

            <footer>
                <p>© 2025 树洞 | 心理援助热线：12320（全国）</p>
            </footer>
        </div>

        <script>
            let progressTimer = null;
            const MAX_POLL = 120;
            let pollCount = 0;

            function switchMode() {
                const sliderBox = document.getElementById("slider_box");
                const presetBox = document.getElementById("preset_box");
                const mode = document.getElementById("custom_mode").value;
                const tipDom = document.getElementById("mode_tip");
                const cloneTipDom = document.getElementById("clone_warning");
                const dataDom = document.getElementById("custom_data");

                if (mode === "clone") {
                    sliderBox.style.display = "none";
                    presetBox.style.display = "none";
                    tipDom.innerHTML = `
                        <i class="fa-solid fa-lightbulb"></i>
                        <span>示例：用户：今天好累 好友：累了就歇会儿～慢慢来嘛，我在呢～</span>
                    `;
                    dataDom.placeholder = "请粘贴参考文本（≥50字）";
                    cloneTipDom.style.display = "flex";
                } else {
                    sliderBox.style.display = "block";
                    presetBox.style.display = "flex";
                    tipDom.innerHTML = `
                        <i class="fa-solid fa-lightbulb"></i>
                        <span>示例：温柔度90，毒舌度10，共情方式是倾听鼓励，口头禅"没关系呀"</span>
                    `;
                    dataDom.placeholder = "请输入性格描述";
                    cloneTipDom.style.display = "none";
                }
            }

            function getProgressText(percent, mode) {
                const stepMap = {
                    0: { text: "初始化", icon: "circle-notch" },
                    10: { text: "校验参数", icon: "check-circle" },
                    20: { text: "准备数据", icon: "database" },
                    30: { text: "预处理完成", icon: "cog" },
                    40: { text: mode === "clone" ? "分析参考风格" : "提取性格特征", icon: "search" },
                    45: { text: mode === "clone" ? "提取核心风格" : "提取核心性格", icon: "filter" },
                    50: { text: mode === "clone" ? "AI分析风格" : "AI分析性格", icon: "brain" },
                    55: { text: mode === "clone" ? "风格分析完成" : "性格分析完成", icon: "chart-line" },
                    60: { text: mode === "clone" ? "风格特征提取完成" : "性格特征提取完成", icon: "list-check" },
                    70: { text: mode === "clone" ? "生成复刻Prompt" : "生成定制Prompt", icon: "magic" },
                    75: { text: mode === "clone" ? "优化复刻Prompt" : "优化定制Prompt", icon: "wand-magic-sparkles" },
                    80: { text: "调用AI生成Prompt", icon: "robot" },
                    85: { text: "Prompt生成完成", icon: "check-double" },
                    90: { text: mode === "clone" ? "复刻完成" : "定制完成", icon: "sparkles" },
                    95: { text: "保存数据", icon: "save" },
                    100: { text: mode === "clone" ? "风格复刻成功" : "性格定制成功", icon: "party-horn" },
                    "-1": { text: "处理失败", icon: "triangle-exclamation" }
                };

                const step = stepMap[percent] || { text: "处理中", icon: "spinner" };
                return {
                    label: `进度：${percent}%`,
                    step: `<i class="fa-solid fa-${step.icon}"></i> <span>${step.text}</span>`
                };
            }

            function pollProgress(user_id, mode) {
                const progressContainer = document.getElementById("progress_container");
                const progressBar = document.getElementById("progress_bar_fill");
                const progressLabel = document.getElementById("progress_label");
                const progressStep = document.getElementById("progress_step");

                pollCount = 0;
                progressBar.style.width = "0%";

                // 显示进度条
                setTimeout(() => progressContainer.classList.add("show"), 50);

                progressTimer = setInterval(async () => {
                    if (pollCount >= MAX_POLL) {
                        clearInterval(progressTimer);
                        progressTimer = null;
                        progressLabel.textContent = "进度：超时";
                        progressStep.innerHTML = "<i class='fa-solid fa-clock-rotate-left'></i> 请刷新重试";
                        showResult(false, "定制超时：网络响应过慢");
                        return;
                    }

                    try {
                        const resp = await fetch(`/get_customize_progress?user_id=${user_id}`);
                        const res = await resp.json();
                        const percent = res.progress;

                        // 更新进度条
                        progressBar.style.width = percent + "%";

                        // 更新文本
                        const progressData = getProgressText(percent, mode);
                        progressLabel.textContent = progressData.label;
                        progressStep.innerHTML = progressData.step;

                        if (percent === 100 || percent === -1) {
                            clearInterval(progressTimer);
                            progressTimer = null;
                            showResult(percent === 100, 
                                percent === 100 ? 
                                `${mode === "clone" ? "风格复刻成功" : "性格定制成功"}！可开始聊天` : 
                                "处理失败：请检查输入后重试"
                            );
                                if (percent === 100) {
                                    fetchGreetingOnce();
                                }
                            // 3秒后自动隐藏
                            setTimeout(() => {
                                progressContainer.classList.remove("show");
                            }, 3000);
                        }
                        pollCount++;
                    } catch (e) {
                        clearInterval(progressTimer);
                        progressTimer = null;
                        progressLabel.textContent = "进度：查询失败";
                        progressStep.innerHTML = "<i class='fa-solid fa-xmark-circle'></i> 网络错误";
                    }
                }, 50);
            }

            function showResult(success, message) {
                const resultDom = document.getElementById("custom_result");
                resultDom.className = `result show ${success ? 'success' : 'error'}`;
                resultDom.innerHTML = `
                    <i class="fa-solid fa-${success ? 'check-circle' : 'circle-xmark'}"></i>
                    ${message}
                `;
            }

            async function customizeAI() {
                const user_id = document.getElementById("user_id").value.trim();
                const mode = document.getElementById("custom_mode").value;
                const data = document.getElementById("custom_data").value.trim();
                const btn = document.getElementById("custom_btn");
                const resultDom = document.getElementById("custom_result");

                // 重置状态
                resultDom.className = "result";
                resultDom.innerHTML = "";
                btn.disabled = true;
                btn.innerHTML = "<i class='fa-solid fa-circle-notch fa-spin'></i> 处理中...";

                // 校验
                if (!user_id) {
                    btn.disabled = false;
                    btn.innerHTML = "<i class='fa-solid fa-check'></i> 确认定制";
                    showResult(false, "❌ 用户ID不能为空");
                    return;
                }
                if (!data) {
                    btn.disabled = false;
                    btn.innerHTML = "<i class='fa-solid fa-check'></i> 确认定制";
                    showResult(false, `❌ 请输入${mode === "clone" ? "参考文本" : "性格描述"}`);
                    return;
                }
                if (mode === "clone" && data.length < 50) {
                    btn.disabled = false;
                    btn.innerHTML = "<i class='fa-solid fa-check'></i> 确认定制";
                    showResult(false, "❌ 克隆模式参考文本需≥50字");
                    return;
                }

                try {
                    // 初始化进度
                    await fetch(`/set_progress?user_id=${user_id}&progress=0`);

                    // 启动轮询
                    pollProgress(user_id, mode);

                    // 延迟确保轮询启动
                    await new Promise(resolve => setTimeout(resolve, 200));

                    // 发送定制请求
                    const resp = await fetch("/customize", {
                        method: "POST",
                        headers: {"Content-Type": "application/json"},
                        body: JSON.stringify({user_id, mode, data})
                    });
                    const res = await resp.json();

                    // 恢复按钮
                    setTimeout(() => {
                        btn.disabled = false;
                        btn.innerHTML = "<i class='fa-solid fa-check'></i> 确认定制";
                        if (!res.success) {
                            showResult(false, `❌ 定制失败：${res.message}`);
                        }
                    }, 500);

                } catch (e) {
                    if (progressTimer) {
                        clearInterval(progressTimer);
                        progressTimer = null;
                    }
                    btn.disabled = false;
                    btn.innerHTML = "<i class='fa-solid fa-check'></i> 确认定制";
                    document.getElementById("progress_container").classList.remove("show");
                    showResult(false, `❌ 请求失败：${e.message}`);
                }
            }

            async function sendChat() {
                const user_id = document.getElementById("user_id").value.trim();
                const input = document.getElementById("chat_input").value.trim();
                const historyDom = document.getElementById("chat_history");
                const btn = document.getElementById("chat_btn");

                if (!user_id) {
                    alert("请先输入用户ID并完成AI定制");
                    return;
                }
                if (!input) {
                    alert("请输入想倾诉的内容");
                    return;
                }

                // 添加用户消息
                historyDom.innerHTML += `
                    <div class="chat-msg user">
                        <div class="chat-bubble">${escapeHtml(input)}</div>
                    </div>
                `;
                document.getElementById("chat_input").value = "";
                historyDom.scrollTop = historyDom.scrollHeight;

                // 显示AI加载
                const aiLoadId = "ai_load_" + Date.now();
                historyDom.innerHTML += `
                    <div class="chat-msg ai" id="${aiLoadId}">
                        <div class="chat-loading">
                            <i class="fa-solid fa-ellipsis fa-beat-fade"></i>
                            <span>AI正在回复...</span>
                        </div>
                    </div>
                `;
                historyDom.scrollTop = historyDom.scrollHeight;
                btn.disabled = true;
                btn.innerHTML = "<i class='fa-solid fa-paper-plane'></i> 发送中...";

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
                    const aiDom = document.getElementById(aiLoadId);
                    aiDom.innerHTML = '<div class="chat-bubble"></div>';
                    const bubbleDom = aiDom.querySelector(".chat-bubble");

                    while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;
                        const char = decoder.decode(value, { stream: true });
                        if (char) {
                            aiReply += char;
                            bubbleDom.textContent = aiReply;
                            historyDom.scrollTop = historyDom.scrollHeight;
                        }
                    }

                    if (!aiReply) {
                        bubbleDom.textContent = "抱歉，暂时无法回复，请稍后再试";
                    }

                } catch (e) {
                    const aiDom = document.getElementById(aiLoadId);
                    aiDom.innerHTML = `<div class="chat-bubble">😥 请求失败：${escapeHtml(e.message)}</div>`;
                } finally {
                    btn.disabled = false;
                    btn.innerHTML = "<i class='fa-solid fa-paper-plane'></i> 发送";
                }
            }

            // 工具函数：转义HTML
            function escapeHtml(text) {
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            }

            // 清理定时器
            window.addEventListener("beforeunload", () => {
                if (progressTimer) {
                    clearInterval(progressTimer);
                    progressTimer = null;
                }
            });
            async function fetchGreetingOnce() {
                const user_id = document.getElementById("user_id").value.trim();
                if (!user_id) return;
            
                try {
                    const resp = await fetch(`/greeting?user_id=${user_id}`);
                    const data = await resp.json();
                    if (data.text) {
                        const historyDom = document.getElementById("chat_history");
                        historyDom.innerHTML += `
                            <div class="chat-msg ai">
                                <div class="chat-bubble">${escapeHtml(data.text)}</div>
                            </div>
                        `;
                        historyDom.scrollTop = historyDom.scrollHeight;
                    }
                } catch (e) {
                    console.error("greeting failed", e);
                }
            }
            // 快捷键
            document.getElementById("chat_input").addEventListener("keydown", (e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    sendChat();
                }
            });
            /* ===== 捏人模式 · 性格预设 ===== */
            const PRESET_SLIDER_MAP = {
                gentle: {
                    gentle: 90,
                    rational: 40,
                    companion: 85,
                    tsundere: 5
                },
                rational: {
                    gentle: 40,
                    rational: 90,
                    companion: 40,
                    tsundere: 10
                },
                tsundere: {
                    gentle: 60,
                    rational: 60,
                    companion: 50,
                    tsundere: 60
                },
                friend: {
                    gentle: 70,
                    rational: 50,
                    companion: 80,
                    tsundere: 20
                },
                listener: {
                    gentle: 80,
                    rational: 30,
                    companion: 90,
                    tsundere: 0
                }
            };
            const PRESET_MAP = {
                gentle: `温柔、耐心、共情能力强。
            说话语气轻柔，不说教。
            多安慰、多陪伴，
            像一个安全可靠的树洞。`,

                rational: `理性冷静，逻辑清晰。
            善于分析问题本质，
            给出结构化建议，
            不过度情绪化。`,

                tsundere: `表面有点毒舌，
            但内心关心用户。
            可以吐槽但不攻击，
            关键时刻会站在用户这边。`,

                friend: `像多年好友一样聊天，
            语气自然随和，
            会接话、会调侃，
            让人感到陪伴。`,

                listener: `以倾听为主，
            少下结论，
            多用共情与确认，
            鼓励用户表达真实感受。`
            };

            function applyPreset(key) {
                const preset = PRESET_SLIDER_MAP[key];
                if (!preset) return;

                // 设置滑块
                document.getElementById("gentle").value = preset.gentle;
                document.getElementById("rational").value = preset.rational;
                document.getElementById("companion").value = preset.companion;
                document.getElementById("tsundere").value = preset.tsundere;

                // 同步生成性格描述
                updatePersonality();
            }
            function updatePersonality() {
            const g = +document.getElementById("gentle").value;
            const r = +document.getElementById("rational").value;
            const c = +document.getElementById("companion").value;
            const t = +document.getElementById("tsundere").value;

            document.getElementById("val_gentle").textContent = g;
            document.getElementById("val_rational").textContent = r;
            document.getElementById("val_companion").textContent = c;
            document.getElementById("val_tsundere").textContent = t;

            let desc = [];

            desc.push(`温柔度 ${g}，${g > 70 ? "语气非常温和" : g > 40 ? "语气偏温和" : "语气偏直接"}`);
            desc.push(`理性度 ${r}，${r > 70 ? "善于分析问题" : r > 40 ? "适度给建议" : "少分析多共情"}`);
            desc.push(`陪伴感 ${c}，${c > 70 ? "强陪伴型回应" : c > 40 ? "会持续跟进" : "不过度黏人"}`);
            desc.push(`毒舌度 ${t}，${t > 60 ? "允许吐槽但不攻击" : t > 30 ? "偶尔轻微吐槽" : "几乎不毒舌"}`);

            desc.push("整体目标：让用户感到被理解、被陪伴、被尊重，不制造压力。");

            document.getElementById("custom_data").value = desc.join("，") + "。";
        }
            document.addEventListener("DOMContentLoaded", () => {
            updatePersonality();
        });
        </script>
    </body>
    </html>
    """

