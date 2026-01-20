import requests
import json
import time
from typing import Generator

from config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_MODEL,
    DEEPSEEK_API_URL,
    MAX_HISTORY,
    SENSITIVE_WORDS,
    STREAM_DELAY
)

from data_store import (
    load_user_data,
    save_user_data,
    add_user_memory,
    get_user_memory_text
)

# =========================================================
# 安全检测
# =========================================================

def check_sensitive(text: str):
    for word in SENSITIVE_WORDS:
        if word in text:
            if word in ["自杀", "自残"]:
                return True, "生命宝贵！心理援助热线：12320（全国）"
            return True, "内容包含违规词，请换个说法"
    return False, ""


# =========================================================
# 捏人模式（Create）
# =========================================================

def extract_personality_for_create(user_description: str) -> dict:
    """
    把用户的性格描述，抽取为结构化人格信息
    """
    prompt = f"""
请根据用户描述，提取人格特征，输出严格 JSON，不要解释：

用户描述：
{user_description}

字段：
- 情绪特点
- 共情方式
- 回复风格
- 口头禅（数组）
- 语气强度
"""

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4,
        "max_tokens": 600
    }

    try:
        resp = requests.post(
            DEEPSEEK_API_URL,
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
            json=payload,
            timeout=60
        )
        return json.loads(resp.json()["choices"][0]["message"]["content"])
    except Exception:
        return {}


# =========================================================
# 行为规则构建（关键）
# =========================================================

def build_behavior_rules(p: dict) -> str:
    """
    把“性格描述” → 强制行为规则（直接给出行为许可/禁令）
    这是人格差异的核心，不再是温柔的选修课。
    """
    rules = []

    # 获取传递的性格文本
    text = " ".join(str(v) for v in p.values() if v)

    # ===== 毒舌 / 高攻击性 =====
    if any(k in text for k in ["毒舌度", "直接吐槽", "反问", "不需要先安慰"]):
        rules += [
            "【强制】当用户的问题空泛、逃避或只是表达无聊时，必须先指出问题本身的空泛，而不是直接给建议。",
            "【强制】可以使用反问句来逼迫用户澄清想法，打破模糊表述。",
            "【强制】不允许使用“你可以试试”“也许可以”这种模糊建议语句。",
            "【强制】必须直言指出问题所在，不使用“安慰”的口吻。",
            "【强制】如果用户显得不想面对问题，必须戳穿并要求进一步明确。"
        ]

    # ===== 强理性 =====
    if any(k in text for k in ["理性度", "直接给出判断", "不需要安慰性语言"]):
        rules += [
            "【强制】可以跳过情绪安慰，直接进入问题分析，不绕圈子。",
            "【强制】允许给出明确的结论，而不是模糊的安慰性语言。",
            "【强制】当用户逻辑不清楚时，必须直接指出问题的矛盾或不合理之处。",
            "【强制】不允许对无关的情绪或状态做无意义的安慰，重点分析问题。"
        ]

    # ===== 温柔 / 共情优先（选项） =====
    if any(k in text for k in ["温柔度", "共情", "情感支持"]):
        rules += [
            "【可选】优先共情用户，确认其情绪和感受，但不需要过度安慰。",
            "【可选】如果用户显得脆弱，可以适度提供情感支持，但不应软化论点。",
            "【可选】避免直接否定用户的感受，尽量理解他们的情绪。"
        ]

    # 如果没有设置任何规则（避免返回空字符串）
    if not rules:
        return ""

    # 返回生成的行为规则，确保行为约束被执行
    return "\n【行为规则｜必须遵守】\n" + "\n".join(f"- {r}" for r in rules)



def generate_system_prompt_create(p: dict) -> str:
    """
    生成最终 system prompt（捏人模式）
    """
    base = f"""
            你是一个正在与用户真实交流的 AI，而不是心理咨询模板。
            
            【人格特征】
            情绪特点：{p.get("情绪特点", "")}
            共情方式：{p.get("共情方式", "")}
            回复风格：{p.get("回复风格", "")}
            口头禅：{",".join(p.get("口头禅", []))}
            语气强度：{p.get("语气强度", "")}
            
            【基础原则】
            - 不必讨好用户
            - 不需要每句话都共情
            - 可以真实表达观点
            - 不暴露你是模型
            """

    return base + build_behavior_rules(p)


# =========================================================
# 克隆模式（Clone）
# =========================================================

def extract_personality_for_clone(reference_text: str) -> dict:
    prompt = f"""
            请分析以下文本的说话风格，并输出严格 JSON，不要解释：
            
            文本：
            {reference_text}
            
            字段：
            - 语气特点
            - 常用词汇（数组）
            - 句式特点
            - 高频口头禅（数组）
            """

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 800
    }

    try:
        resp = requests.post(
            DEEPSEEK_API_URL,
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
            json=payload,
            timeout=60
        )
        return json.loads(resp.json()["choices"][0]["message"]["content"])
    except Exception:
        return {}


def generate_system_prompt_clone(p: dict) -> str:
    return f"""
你将严格模仿以下说话风格进行回复：

语气特点：{p.get("语气特点", "")}
句式特点：{p.get("句式特点", "")}
常用词汇：{",".join(p.get("常用词汇", []))}
高频口头禅：{",".join(p.get("高频口头禅", []))}

规则：
- 用词、语气、句式必须一致
- 不解释风格来源
- 不自我暴露
"""


# =========================================================
# 聊天主逻辑
# =========================================================

def stream_chat_with_deepseek(
    user_id: str,
    user_input: str
) -> Generator[str, None, None]:

    # ---------- 1. 安全检测 ----------
    unsafe, warning = check_sensitive(user_input)
    if unsafe:
        for c in warning:
            yield c
            time.sleep(STREAM_DELAY)
        return

    # ---------- 2. 用户数据 ----------
    user_info = load_user_data(user_id)
    plan = user_info.get("plan", "free")

    # 免费额度控制
    if plan == "free":
        count = user_info.get("chat_count", 0)
        if count >= 20:
            tip = "今天的免费聊天次数已用完，可以升级获得更多陪伴 🌱"
            for c in tip:
                yield c
                time.sleep(STREAM_DELAY)
            return
        user_info["chat_count"] = count + 1
        save_user_data(user_id, user_info)

    base_prompt = user_info.get("system_prompt", "")

    # ---------- 3. 套餐级行为规则 ----------
    if plan == "pro":
        system_prompt = base_prompt + """
        【模式规则 · 深度引导】
        - 可以主动追问
        - 可以挑战用户的叙事
        - 不满足于表层情绪
        """
    elif plan == "plus":
        system_prompt = base_prompt + """
        【模式规则 · 陪伴】
        - 可以主动延续话题
        - 保持回应连续性
        """
    else:
        system_prompt = base_prompt + """
        【模式限制 · 免费】
        - 不进行长篇分析
        - 不连续追问
        - 保持单轮回应
        """

    history = user_info.get("history", [])

    # ---------- 4. 主动问候 ----------
    if plan in ["plus", "pro"] and not user_info.get("has_greeted"):
        greet = "我在这。你可以直接说，不用整理得多好。"
        history.append({"role": "assistant", "content": greet})
        user_info["has_greeted"] = True
        user_info["history"] = history
        save_user_data(user_id, user_info)

    # ---------- 5. 构造消息 ----------
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": get_user_memory_text(user_id)},
    ]

    for h in history[-MAX_HISTORY * 2:]:
        messages.append(h)

    messages.append({"role": "user", "content": user_input})

    # ---------- 6. 调用 DeepSeek ----------
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "stream": True,
        "temperature": 0.75
    }

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    full_reply = ""

    try:
        with requests.post(
            DEEPSEEK_API_URL,
            headers=headers,
            json=payload,
            stream=True,
            timeout=60
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line:
                    continue
                line = line.decode("utf-8")
                if not line.startswith("data:"):
                    continue

                data = line.replace("data:", "").strip()
                if data == "[DONE]":
                    break

                chunk = json.loads(data)
                delta = chunk["choices"][0]["delta"].get("content", "")
                if delta:
                    full_reply += delta
                    yield delta
                    time.sleep(STREAM_DELAY)

    except Exception:
        err = "（对话异常，请稍后再试）"
        for c in err:
            yield c
            time.sleep(STREAM_DELAY)
        return

    # ---------- 7. 写回历史 ----------
    history.append({"role": "user", "content": user_input})
    history.append({"role": "assistant", "content": full_reply})
    user_info["history"] = history[-MAX_HISTORY * 2:]

    # ---------- 8. 记忆抽取 ----------
    if any(k in user_input for k in ["我叫", "我是", "我一直", "我总是", "我已经"]):
        add_user_memory(user_id, user_input)

    save_user_data(user_id, user_info)
