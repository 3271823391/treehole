import os
import json
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
# ===============================
# 情绪分析去重缓存（按轮次）
# ===============================
_last_emotion_round = {}
_last_emotion_result = {}

ARK_API_KEY = os.getenv("ARK_API_KEY")
ARK_URL = "https://ark.cn-beijing.volces.com/api/v3/responses"
MODEL_ID = "deepseek-v3-2-251201"


# ===============================
# 请求模型（HTTP 用）
# ===============================

class EmotionRequest(BaseModel):
    history: list
    current_input: str
    round_id: int
# ===============================
# 核心逻辑（给 Python / chat_core 用）
# ===============================
@router.post("/emotion")
def analyze_emotion(req: EmotionRequest):
    round_id = req.round_id

    # ⚠️ demo 版：单用户，直接用固定 key
    user_key = "default"

    last_round = _last_emotion_round.get(user_key)

    if last_round == round_id:
        # 命中重复轮次，直接返回上一次结果
        return _last_emotion_result[user_key]

    history = req.history
    current_input = req.current_input

    # 1️⃣ 拼上下文文本（这是你真正想要的）
    context_text = "\n".join(
        [h["content"] for h in history if h.get("role") == "user"]
        + [current_input]
    )

    payload = {
        "model": MODEL_ID,
        "input": [
            {
                "role": "system",
                "content": [{
                    "type": "input_text",
                    "text": (
                        "你是一个【情绪分析引擎】，不是聊天机器人。\n"
                        "你的职责是基于【对话上下文 + 当前输入】进行情绪分析，而不是与用户互动。\n"
                        "你必须将上下文视为情绪背景，用于判断当前文本的真实情绪倾向。\n\n"
                    
                        "【一、上下文使用规则（非常重要）】\n"
                        "- 系统会向你提供一段对话上下文以及当前用户输入\n"
                        "- 上下文用于理解情绪演变、语境和隐含态度\n"
                        "- score 必须基于【当前输入在上下文中的情绪含义】给出\n"
                        "- 不得只根据当前一句话做孤立判断\n"
                        "- 如果当前输入本身中性，但结合上下文存在明确情绪延续，允许 score 偏离 50\n\n"
                    
                        "【二、输出格式要求】\n"
                        "- 你只能输出一个 JSON 对象\n"
                        "- 不得输出任何解释、前言、Markdown、注释或多余文本\n"
                        "- 输出内容必须是可被直接解析的合法 JSON\n\n"
                    
                        "【三、情绪评分规则】\n"
                        "- score 表示情绪倾向评分，取值范围为 0–100\n"
                        "- 50 表示中性情绪，这是默认值\n"
                        "- 0 表示极端负面情绪，100 表示极端正面情绪\n"
                        "- 中性情绪不等于 0，0 绝不代表中性\n"
                        "- 仅当上下文或当前文本中出现明确情绪态度、情绪强度或持续情绪趋势时，才允许 score 偏离 50\n\n"
                    
                        "【四、tags 规则】\n"
                        "- tags 是一个字符串数组\n"
                        "- 中性内容必须包含 \"中性\"\n"
                        "- 标签应反映上下文中的主要情绪类型\n"
                        "- 不得生成与上下文和当前输入无关的标签\n\n"
                    
                        "【五、analysis 规则】\n"
                        "- analysis 描述【结合上下文后】文本体现的情绪特征\n"
                        "- 允许提及情绪延续、情绪变化或情绪对比\n"
                        "- 语气应接近客观观察记录或分析总结\n"
                        "- 不进行共情、不安慰、不评价用户\n"
                        "- 不直接对用户说话，不使用“你”\n"
                        "- 不得出现“该用户”“文本提到”等修饰词\n"
                        "- 使用第三人称进行客观描述\n\n"
                    
                        "【六、suggestion 规则】\n"
                        "- suggestion 基于整体情绪状态给出克制、客观的建议\n"
                        "- 中性情绪只能给出中性、引导式建议\n"
                        "- 允许口语化表达，但不得使用安慰性、情绪化或鼓励性措辞\n"
                        "- 不使用“别担心”“没关系”“可以理解”等表述\n\n"
                    
                        "【七、禁止事项】\n"
                        "- 不得解释你的推理过程\n"
                        "- 不得输出 reasoning 或类似字段\n"
                        "- 不得擅自修改评分含义\n"
                        "- 不得将“中性”情绪视为 0 分\n\n"
                    
                        "本任务为快速结构化分析任务，不需要深入推理或反思。\n"
                        "请直接基于上下文和规则给出结果，优先保证速度与一致性。"
                    )
                }]
            },
            {
                "role": "user",
                "content": [{
                    "type": "input_text",
                    "text": context_text
                }]
            }
        ]
    }

    r = requests.post(
        ARK_URL,
        headers={
            "Authorization": f"Bearer {ARK_API_KEY}",
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=30
    )

    r.raise_for_status()
    seed_json = r.json()
    print("SEED RAW:", seed_json)
    # 2️⃣ 解析返回
    for item in seed_json.get("output", []):
        if item.get("type") == "message":
            text = item["content"][0]["text"]
            result = json.loads(text)

            _last_emotion_round[user_key] = round_id
            _last_emotion_result[user_key] = result

            return result

    raise RuntimeError("Emotion JSON parse failed")
