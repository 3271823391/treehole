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

app = FastAPI(title="DeepSeek流式虚拟树洞（修复进度条跳变）")


# 定义参数模型
class CustomizeRequest(BaseModel):
    user_id: str
    mode: str
    data: str


class ChatStreamRequest(BaseModel):
    user_id: str
    user_input: str


# 前端页面（核心修复：先轮询后请求）
@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
    <head><title>DeepSeek流式虚拟树洞（修复进度条）</title>
    <style>
        body{max-width:800px;margin:0 auto;padding:20px;font-family:Arial;}
        .section{margin:20px 0;padding:20px;border:1px solid #eee;border-radius:8px;}
        button{background:#007bff;color:white;border:none;padding:10px 20px;border-radius:4px;cursor:pointer;}
        button:hover{background:#0056b3;}
        input, textarea{width:100%;padding:10px;margin:10px 0;border:1px solid #ddd;border-radius:4px;box-sizing:border-box;}
        #custom_result{margin-top:10px;color:#dc3545;}
        #chat_history p{margin:5px 0;}
        #chat_history .user{color:#007bff;}
        #chat_history .ai{color:#28a745;}
        .typing::after{content:'...';animation: typing 1s infinite;}
        @keyframes typing {
            0% {content: '.';}
            50% {content: '..';}
            100% {content: '...';}
        }

        /* 进度条样式 */
        .progress-container {
            width: 100%;
            height: 8px;
            background: #f0f0f0;
            border-radius: 4px;
            margin: 10px 0;
            display: none;
            overflow: hidden;
        }
        .progress-bar {
            height: 100%;
            width: 0%;
            background: #007bff;
            border-radius: 4px;
            transition: width 0.1s ease;
        }
        .progress-bar.error {background: #dc3545;}
        .progress-bar.success {background: #28a745;}
        .progress-text {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
            display: none;
        }
        .mode-tip {font-size: 12px;color: #999;margin: -5px 0 10px 0;}
        .clone-tip {color: #ff6700;font-weight: bold;}
    </style></head>
    <body>
    <h1>DeepSeek流式虚拟树洞（修复进度条）</h1>

    <div class="section">
    <h2>1. 定制AI性格</h2>
    <input type="text" id="user_id" placeholder="输入你的用户ID（如test001）" required>
    <select id="custom_mode" onchange="changeModeTip()">
        <option value="捏人">捏人模式（自定义性格）</option>
        <option value="clone">克隆模式（复刻参考文本风格）</option>
    </select>
    <div id="mode_tip" class="mode-tip">
        捏人模式：输入性格描述（如“温柔度90，毒舌度10，共情方式是倾听和鼓励”）
    </div>
    <textarea id="custom_data" placeholder="捏人模式示例：温柔度90，毒舌度10，共情方式是倾听和鼓励，回复用中句，口头禅是没关系呀" rows="5"></textarea>
    <div id="clone_warning" class="clone-tip" style="display:none;">
        克隆模式要求：参考文本长度≥50字（如粘贴1-3段聊天记录/语气示例）
    </div>
    <button onclick="customizeCharacter()">确认定制</button>

    <div id="custom_progress" class="progress-container">
        <div id="progress_bar" class="progress-bar"></div>
    </div>
    <div id="progress_text" class="progress-text">进度：0%（初始化）</div>
    <div id="custom_result"></div>
    </div>

    <div class="section">
    <h2>2. 开始聊天（逐字生成）</h2>
    <textarea id="chat_input" placeholder="输入想倾诉的话..." rows="3"></textarea>
    <button onclick="sendStreamChat()">发送</button>
    <div id="chat_history" style="margin-top:10px;height:300px;overflow-y:auto;border:1px solid #eee;padding:10px;"></div>
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
            modeTip.innerText = "克隆模式：粘贴参考文本（如聊天记录/语气示例），AI将100%复刻其说话风格";
            customData.placeholder = "克隆模式示例：\\n用户：今天好累啊\\n好友：累了就歇会儿呗～多大点事儿，反正慢慢来嘛，总会好的😜\\n用户：感觉啥都做不好\\n好友：别瞎想啦！你已经很棒了，我一直都在的～";
            cloneWarning.style.display = "block";
        } else {
            modeTip.innerText = "捏人模式：输入性格描述（如“温柔度90，毒舌度10，共情方式是倾听和鼓励”）";
            customData.placeholder = "捏人模式示例：温柔度90，毒舌度10，共情方式是倾听和鼓励，回复用中句，口头禅是没关系呀";
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

    // 轮询进度（核心：高频轮询）
    function pollProgress(user_id, mode) {
        const progressBar = document.getElementById("progress_bar");
        const progressText = document.getElementById("progress_text");

        // 手动先渲染0%，避免卡顿
        progressBar.style.width = "0%";
        progressText.innerText = getProgressText(0, mode);

        // 50ms一次轮询（极致高频）
        progressTimer = setInterval(async () => {
            try {
                const resp = await fetch(`/get_customize_progress?user_id=${user_id}`);
                const res = await resp.json();
                const percent = res.progress;

                // 强制更新进度条和文本
                progressBar.style.width = `${Math.max(0, percent)}%`;
                progressText.innerText = getProgressText(percent, mode);

                // 结束轮询条件
                if (percent === 100 || percent === -1) {
                    clearInterval(progressTimer);
                    progressBar.classList.add(percent === 100 ? "success" : "error");
                }
            } catch (e) {
                clearInterval(progressTimer);
                progressText.innerText = "进度：查询失败";
            }
        }, 50); // 50ms一次，确保不遗漏任何进度节点
    }

    // 核心修复：先启动轮询，延迟300ms再发起后端请求
    async function customizeCharacter() {
        const user_id = document.getElementById("user_id").value.trim();
        const mode = document.getElementById("custom_mode").value;
        const data = document.getElementById("custom_data").value.trim();
        const resultDom = document.getElementById("custom_result");
        const progressContainer = document.getElementById("custom_progress");
        const progressBar = document.getElementById("progress_bar");
        const progressText = document.getElementById("progress_text");

        // 重置状态
        resultDom.innerText = "";
        progressBar.className = "progress-bar";
        progressContainer.style.display = "block";
        progressText.style.display = "block";

        // 清除旧定时器
        if (progressTimer) clearInterval(progressTimer);

        // 基础校验
        if (!user_id) {
            progressContainer.style.display = "none";
            progressText.style.display = "none";
            resultDom.innerText = "错误：用户ID不能为空";
            return;
        }
        if (!data) {
            progressContainer.style.display = "none";
            progressText.style.display = "none";
            resultDom.innerText = "错误：请输入" + (mode === "clone" ? "参考文本" : "性格描述");
            return;
        }
        if (mode === "clone" && data.length < 50) {
            progressContainer.style.display = "none";
            progressText.style.display = "none";
            resultDom.innerText = "错误：克隆模式参考文本长度需≥50字";
            return;
        }

        try {
            // 步骤1：初始化后端进度为0
            await fetch(`/set_progress?user_id=${user_id}&progress=0`);

            // 步骤2：启动轮询（此时进度是0，前端先渲染）
            pollProgress(user_id, mode);

            // 步骤3：延迟300ms，让轮询稳定运行后再发起后端请求
            await new Promise(resolve => setTimeout(resolve, 300));

            // 步骤4：发起定制请求（此时轮询已经在运行，能捕获所有进度）
            const resp = await fetch("/customize", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({user_id, mode, data})
            });

            const res = await resp.json();
            if (res.success) {
                resultDom.innerText = res.message;
                resultDom.style.color = "#28a745";
            } else {
                resultDom.innerText = "定制失败：" + (res.message || "未知错误");
                resultDom.style.color = "#dc3545";
                progressBar.classList.add("error");
            }

            // 延迟隐藏进度条
            setTimeout(() => {
                progressContainer.style.display = "none";
                progressText.style.display = "none";
            }, 2000);
        } catch (e) {
            if (progressTimer) clearInterval(progressTimer);
            progressBar.classList.add("error");
            progressText.innerText = "进度：失败（" + e.message + "）";
            resultDom.innerText = "请求失败：" + e.message;
            resultDom.style.color = "#dc3545";

            setTimeout(() => {
                progressContainer.style.display = "none";
                progressText.style.display = "none";
            }, 2000);
        }
    }

    // 流式聊天函数（不变）
    async function sendStreamChat() {
        const user_id = document.getElementById("user_id").value.trim();
        const input = document.getElementById("chat_input").value.trim();
        const historyDom = document.getElementById("chat_history");

        if (!user_id) {
            alert("请先输入用户ID并完成性格定制");
            return;
        }
        if (!input) {
            alert("请输入想倾诉的内容");
            return;
        }

        historyDom.innerHTML += `<p class="user">你：${input}</p>`;
        document.getElementById("chat_input").value = "";
        historyDom.scrollTop = historyDom.scrollHeight;

        const aiReplyId = "ai_reply_" + Date.now();
        historyDom.innerHTML += `<p class="ai typing" id="${aiReplyId}">AI：</p>`;
        historyDom.scrollTop = historyDom.scrollHeight;

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
            const aiReplyDom = document.getElementById(aiReplyId);

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                const char = decoder.decode(value, { stream: true });
                aiReply += char;
                aiReplyDom.innerText = "AI：" + aiReply;
                aiReplyDom.classList.remove("typing");
                historyDom.scrollTop = historyDom.scrollHeight;
            }
        } catch (e) {
            const aiReplyDom = document.getElementById(aiReplyId);
            aiReplyDom.innerText = "AI：请求失败：" + e.message;
            aiReplyDom.classList.remove("typing");
        }
    }
    </script>
    </body></html>
    """


# 进度接口
@app.get("/set_progress")
async def set_progress(user_id: str, progress: int):
    customize_progress[user_id] = progress
    return JSONResponse({"success": True})


@app.get("/get_customize_progress")
async def get_customize_progress(user_id: str):
    return JSONResponse({
        "progress": customize_progress.get(user_id, 0)
    })


# 定制接口（后端分步延迟）
@app.post("/customize")
async def customize_character(req: CustomizeRequest):
    user_id = req.user_id.strip()
    mode = req.mode.strip()
    data = req.data.strip()
    user_info = load_user_data(user_id)

    try:
        # 初始进度：10→20→30（每个节点0.3秒延迟）
        customize_progress[user_id] = 10
        time.sleep(0.3)
        customize_progress[user_id] = 20
        time.sleep(0.3)
        customize_progress[user_id] = 30
        time.sleep(0.3)

        # 核心处理
        if mode == "clone":
            personality = extract_personality_for_clone(data, user_id)
            system_prompt = generate_system_prompt_clone(personality, user_id)
        else:
            personality = extract_personality_for_create(data, user_id)
            system_prompt = generate_system_prompt_create(personality, user_id)

        # 收尾进度：90→95→100（每个节点0.3秒延迟）
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


# 流式聊天接口
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


# 启动函数
def run_api():
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)