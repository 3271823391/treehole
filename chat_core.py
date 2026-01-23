import requests
import json
import time
import os
from typing import Generator
from pathlib import Path
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

IP_PROMPT_MAP = {
    "linyu": "林屿.txt",
    "suwan": "苏晚.txt",
    "xiaxingmian": "夏星眠.txt",
    "jiangche": "江澈.txt",
    "luchengyu": "陆承宇.txt",
}

# =========================================================
# 安全检测
# =========================================================
def load_ip_prompt(filename: str) -> str:
    """
    从 routers/characters/ 目录读取人物 system prompt
    """
    base_dir = os.path.dirname(__file__)      # routers/
    ip_dir = os.path.join(base_dir, "characters")
    path = os.path.join(ip_dir, filename)

    if not os.path.exists(path):
        raise FileNotFoundError(f"人物 prompt 不存在: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return f.read()


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
            "【强制】当用户提出模糊、空洞或者逃避性的问题时，必须直言指出他们在浪费时间，逼迫其给出具体问题。",
            "【强制】如果用户表达不自信或疑虑，必须反问‘为什么连这个都不敢尝试？’并要求用户面对自己的懦弱。",
            "【强制】当用户提出‘我不确定’或者‘也许可以’的回答时，必须嘲笑其优柔寡断，并强迫其表态。",
            "【强制】如果用户表达‘我做不到’，必须揭露其自我设限，讽刺其没有勇气突破。",
            "【强制】针对用户的回避性回答，必须挑战其现有观点，并要求其提供具体的行动计划，而不是依赖安慰。",
            "【强制】对于用户提出的简单或显而易见的问题，必须直接指出其无知，并让其自我反思。",
            "【强制】当用户表现出情绪化时，必须直指其情绪失控，并批评其情感反应的无意义，要求其理性分析。",
            "【强制】如果用户问‘怎么做’，必须反问‘你自己想不明白吗？’并要求其给出合理的解决方案。"
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

def build_final_system_prompt(
    base_prompt: str,
    plan: str,
    user_id: str
) -> str:
    """
    构建唯一 system prompt（禁止多 system）
    """

    if plan == "pro":
        plan_rules = """
【当前交互模式 · 深度引导】
- 可以主动追问
- 可以挑战用户的叙事
- 不满足于表层情绪
"""
    elif plan == "plus":
        plan_rules = """
【当前交互模式 · 陪伴】
- 可以主动延续话题
- 保持回应连续性
"""
    else:
        plan_rules = """
【当前交互模式 · 免费】
- 不进行长篇分析
- 不连续追问
- 保持单轮回应
"""

    user_memory = get_user_memory_text(user_id)

    return f"""
【角色人物设定 · 不可违背】
{base_prompt}

【用户长期记忆 · 仅供参考】
{user_memory}

{plan_rules}
"""
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
    user_input: str,
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
    ip = user_info.get("ip_name")
    DEFAULT_TREEHOLE_PROMPT = "你是一个匿名树洞，只负责倾听与回应，不绑定任何角色。"

    if ip:
        # ===== IP / 轻语信箱模式 =====
        prompt_file = IP_PROMPT_MAP.get(ip)
        if not prompt_file:
            raise ValueError(f"未知角色 ip_name: {ip}")

        system_prompt = load_ip_prompt(prompt_file)
    else:
        # ===== 自由树洞模式 =====
        system_prompt = DEFAULT_TREEHOLE_PROMPT

    plan = user_info.get("plan", "plus")

    # ---------- 3. 套餐级行为规则 ----------
    system_prompt = build_final_system_prompt(
        base_prompt=base_prompt,
        plan=plan,
        user_id=user_id
    )

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
    ]

    for h in history[-MAX_HISTORY * 2:]:
        if h["role"] == "assistant":
            MODEL_LEAK_WORDS = [
                "我是AI", "我是模型", "作为一个", "作为一名助手",
                "我无法", "我不能替代", "作为语言模型"
            ]

            if h["role"] == "assistant":
                if any(k in h["content"] for k in MODEL_LEAK_WORDS):
                    continue
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
