import requests
import json
import time
from config import (
    DEEPSEEK_API_KEY, DEEPSEEK_MODEL, DEEPSEEK_API_URL,
    MAX_HISTORY, SENSITIVE_WORDS, STREAM_DELAY, customize_progress
)
from data_store import get_user_memory_text


def check_sensitive(text: str) -> tuple[bool, str]:
    """敏感词检查"""
    for word in SENSITIVE_WORDS:
        if word in text:
            if word in ["自杀", "自残"]:
                return True, "生命宝贵！心理援助热线：12320（全国）"
            return True, "发言包含违规内容，请更换话题"
    return False, ""


def extract_personality_for_create(text: str, user_id: str) -> dict:
    """捏人模式：提取性格特征（超分步延迟）"""
    # 进度逐步增长：40% → 45% → 50% → 55% → 60%（每个节点0.3秒延迟）
    customize_progress[user_id] = 40
    time.sleep(0.3)  # 延长延迟到0.3秒
    customize_progress[user_id] = 45
    time.sleep(0.3)

    prompt = f"""分析以下性格描述文本，输出JSON格式的性格特征（仅输出JSON，无其他内容）：
    必须包含字段：
    - 情绪特点：高冷/热情/温和/傲娇/沉稳等
    - 共情方式：倾听/鼓励/理性分析/共情安慰/毒舌吐槽等
    - 回复风格：短句/中句/长句/简洁/啰嗦/口语化/书面化等
    - 口头禅：1-2个符合性格的口头禅（如“没关系呀”“加油哦”）
    - 语气强度：温和/强势/中性/软糯等

    性格描述文本：{text[:3000]}"""
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
    data = {
        "model": DEEPSEEK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500,
        "temperature": 0.4
    }
    try:
        customize_progress[user_id] = 50
        time.sleep(0.3)
        resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=15)
        customize_progress[user_id] = 55
        time.sleep(0.3)

        resp.raise_for_status()
        resp_json = resp.json()
        if "choices" not in resp_json or len(resp_json["choices"]) == 0:
            res = {
                "情绪特点": "温和", "共情方式": "倾听",
                "回复风格": "中句", "口头禅": ["没关系呀"],
                "语气强度": "温和"
            }
        else:
            res = json.loads(resp_json["choices"][0]["message"]["content"].strip())

        customize_progress[user_id] = 60
        time.sleep(0.3)
        return res
    except json.JSONDecodeError:
        customize_progress[user_id] = -1
        return {
            "情绪特点": "温和", "共情方式": "倾听",
            "回复风格": "中句", "口头禅": ["没关系呀"],
            "语气强度": "温和"
        }
    except Exception as e:
        customize_progress[user_id] = -1
        return {
            "情绪特点": "温和", "共情方式": "倾听",
            "回复风格": "中句", "口头禅": ["没关系呀"],
            "语气强度": "温和"
        }


def extract_personality_for_clone(text: str, user_id: str) -> dict:
    """克隆模式：专属风格提取（超分步延迟）"""
    # 进度逐步增长：40% → 45% → 50% → 55% → 60%（每个节点0.3秒延迟）
    customize_progress[user_id] = 40
    time.sleep(0.3)
    customize_progress[user_id] = 45
    time.sleep(0.3)

    prompt = f"""深度分析以下参考文本的说话风格和特征，输出JSON格式（仅输出JSON，无其他内容）：
    必须包含字段（严格复刻参考文本的特征）：
    - 情绪特点：从参考文本中提取（如高冷/热情/温和/傲娇/沙雕等）
    - 共情方式：从参考文本中提取（如倾听/鼓励/理性/毒舌/吐槽等）
    - 回复风格：从参考文本中提取（如短句/长句/口语化/书面化/简洁/啰嗦等）
    - 口头禅：从参考文本中提取1-2个高频出现的口头禅/常用语
    - 语气强度：从参考文本中提取（如温和/强势/中性/软糯/沙雕等）
    - 常用词汇：从参考文本中提取3-5个高频使用的词汇
    - 句式特点：从参考文本中提取（如多用短句/反问句/感叹句/陈述句等）

    参考文本（需完全复刻风格）：{text[:3000]}"""
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
    data = {
        "model": DEEPSEEK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 800,
        "temperature": 0.3
    }
    try:
        customize_progress[user_id] = 50
        time.sleep(0.3)
        resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=20)
        customize_progress[user_id] = 55
        time.sleep(0.3)

        resp.raise_for_status()
        resp_json = resp.json()
        if "choices" not in resp_json or len(resp_json["choices"]) == 0:
            res = {
                "情绪特点": "温和", "共情方式": "倾听",
                "回复风格": "中句", "口头禅": ["嗯"],
                "语气强度": "温和", "常用词汇": ["好的", "加油"],
                "句式特点": "陈述句"
            }
        else:
            res = json.loads(resp_json["choices"][0]["message"]["content"].strip())

        customize_progress[user_id] = 60
        time.sleep(0.3)
        return res
    except json.JSONDecodeError:
        customize_progress[user_id] = -1
        return {
            "情绪特点": "温和", "共情方式": "倾听",
            "回复风格": "中句", "口头禅": ["嗯"],
            "语气强度": "温和", "常用词汇": ["好的", "加油"],
            "句式特点": "陈述句"
        }
    except Exception as e:
        customize_progress[user_id] = -1
        return {
            "情绪特点": "温和", "共情方式": "倾听",
            "回复风格": "中句", "口头禅": ["嗯"],
            "语气强度": "温和", "常用词汇": ["好的", "加油"],
            "句式特点": "陈述句"
        }


def generate_system_prompt_create(personality_json: dict, user_id: str) -> str:
    """捏人模式：生成定制Prompt（超分步延迟）"""
    # 进度逐步增长：70% → 75% → 80% → 85% → 90%（每个节点0.3秒延迟）
    customize_progress[user_id] = 70
    time.sleep(0.3)
    customize_progress[user_id] = 75
    time.sleep(0.3)

    prompt = f"""根据以下性格特征，生成AI树洞的System Prompt（80字内）：
    要求：
    1. 严格按照性格特征回复，语气/风格/口头禅完全匹配
    2. 共情优先，不批判，回复简洁自然
    3. 敏感内容触发心理援助热线提示
    4. 仅输出Prompt文本，无其他内容

    性格特征：{json.dumps(personality_json, ensure_ascii=False)}"""
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
    data = {
        "model": DEEPSEEK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 200,
        "temperature": 0.6
    }
    try:
        customize_progress[user_id] = 80
        time.sleep(0.3)
        resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=15)
        customize_progress[user_id] = 85
        time.sleep(0.3)

        resp.raise_for_status()
        resp_json = resp.json()
        if "choices" not in resp_json or len(resp_json["choices"]) == 0:
            res = "你是一个温和的倾听者，善于共情，回复用中句，口头禅是“没关系呀”，语气温和，不批判，敏感内容提示心理援助热线。"
        else:
            res = resp_json["choices"][0]["message"]["content"].strip()

        customize_progress[user_id] = 90
        time.sleep(0.3)
        return res
    except Exception as e:
        customize_progress[user_id] = -1
        return "你是一个温和的倾听者，善于共情，回复用中句，口头禅是“没关系呀”，语气温和，不批判，敏感内容提示心理援助热线。"


def generate_system_prompt_clone(personality_json: dict, user_id: str) -> str:
    """克隆模式：专属Prompt生成（超分步延迟）"""
    # 进度逐步增长：70% → 75% → 80% → 85% → 90%（每个节点0.3秒延迟）
    customize_progress[user_id] = 70
    time.sleep(0.3)
    customize_progress[user_id] = 75
    time.sleep(0.3)

    prompt = f"""根据以下提取的参考文本风格特征，生成AI树洞的System Prompt（100字内）：
    核心要求：
    1. 100%复刻参考文本的说话风格、语气、口头禅、常用词汇、句式特点
    2. 回复时必须使用提取的口头禅和常用词汇
    3. 句式特点、语气强度完全匹配参考文本
    4. 共情方式贴合参考文本特征，敏感内容触发心理援助热线提示
    5. 仅输出Prompt文本，无其他内容

    风格特征：{json.dumps(personality_json, ensure_ascii=False)}"""
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
    data = {
        "model": DEEPSEEK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 300,
        "temperature": 0.3
    }
    try:
        customize_progress[user_id] = 80
        time.sleep(0.3)
        resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=15)
        customize_progress[user_id] = 85
        time.sleep(0.3)

        resp.raise_for_status()
        resp_json = resp.json()
        if "choices" not in resp_json or len(resp_json["choices"]) == 0:
            res = f"你需要完全复刻以下风格回复：情绪{personality_json['情绪特点']}，语气{personality_json['语气强度']}，口头禅{personality_json['口头禅'][0]}，常用词汇{personality_json['常用词汇'][0]}，句式{personality_json['句式特点']}，共情方式{personality_json['共情方式']}。"
        else:
            res = resp_json["choices"][0]["message"]["content"].strip()

        customize_progress[user_id] = 90
        time.sleep(0.3)
        return res
    except Exception as e:
        customize_progress[user_id] = -1
        return f"你需要完全复刻以下风格回复：情绪{personality_json['情绪特点']}，语气{personality_json['语气强度']}，口头禅{personality_json['口头禅'][0]}，常用词汇{personality_json['常用词汇'][0]}，句式{personality_json['句式特点']}，共情方式{personality_json['共情方式']}。"


def stream_chat_with_deepseek(user_id: str, user_input: str, system_prompt: str, history: list):
    """DeepSeek流式聊天核心函数（不变）"""
    unsafe, warning = check_sensitive(user_input)
    if unsafe:
        for char in warning:
            yield char
            time.sleep(STREAM_DELAY)
        return

    memory_text = get_user_memory_text(user_id)
    final_system_prompt = f"{system_prompt}\n{memory_text}"

    messages = [{"role": "system", "content": final_system_prompt}] + history[-MAX_HISTORY:]
    messages.append({"role": "user", "content": user_input})

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
    data = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "max_tokens": 800,
        "temperature": 0.4,
        "stream": True
    }

    try:
        resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, stream=True, timeout=30)
        resp.raise_for_status()

        full_response = ""
        for line in resp.iter_lines():
            if not line:
                continue
            line = line.decode("utf-8").lstrip("data: ").rstrip()
            if line == "[DONE]":
                break
            try:
                line_json = json.loads(line)
                if "choices" in line_json and len(line_json["choices"]) > 0:
                    delta = line_json["choices"][0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        full_response += content
                        yield content
                        time.sleep(STREAM_DELAY)
            except json.JSONDecodeError:
                continue
            except Exception as e:
                continue

        unsafe, warning = check_sensitive(full_response)
        if unsafe:
            for char in warning:
                yield char
                time.sleep(STREAM_DELAY)
        elif not full_response:
            no_reply = "AI暂时无法回复，请稍后再试～"
            for char in no_reply:
                yield char
                time.sleep(STREAM_DELAY)

    except requests.exceptions.HTTPError as e:
        error_msg = f"请求失败：{str(e)}"
        if "401" in str(e):
            error_msg += "（API密钥错误）"
        elif "402" in str(e):
            error_msg += "（额度用尽）"
        for char in error_msg:
            yield char
            time.sleep(STREAM_DELAY)
    except requests.exceptions.Timeout:
        timeout_msg = "请求超时啦，网络有点慢～"
        for char in timeout_msg:
            yield char
            time.sleep(STREAM_DELAY)
    except Exception as e:
        error_msg = f"回复失败：{str(e)[:20]}"
        for char in error_msg:
            yield char
            time.sleep(STREAM_DELAY)