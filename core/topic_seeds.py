from __future__ import annotations

from core.characters import IP_PROMPT_MAP

FALLBACK_TOPIC_SEEDS: dict[str, list[str]] = {
    "linyu": ["最近压力点", "今天最难受时刻", "想被怎样回应"],
    "suwan": ["当前最想解决", "今晚想放松什么", "想先从哪件事说"],
    "xiaxingmian": ["最近情绪波动", "今天有没有好消息", "想聊聊谁让你在意"],
    "jiangche": ["这件事卡在哪", "下一步最难的是", "你最担心的后果"],
    "jiangan": ["最想被理解的点", "最近睡眠状态", "你现在最缺什么支持"],
    "default": ["你此刻最在意什么", "这件事最难受哪部分", "接下来想先聊哪一点"],
}


def pick_topic_seed(character_id: str | None, topic_seeds: list[str]) -> str:
    cleaned = [seed.strip() for seed in topic_seeds if isinstance(seed, str) and seed.strip()]
    if cleaned:
        return cleaned[0][:12]
    if character_id and character_id in IP_PROMPT_MAP:
        seeds = FALLBACK_TOPIC_SEEDS.get(character_id, FALLBACK_TOPIC_SEEDS["default"])
    else:
        seeds = FALLBACK_TOPIC_SEEDS["default"]
    return seeds[0]
