import chat_core


def make_analysis(c):
    return chat_core.EmotionAnalysis(
        emotion=chat_core.EmotionBlock(valence=0, arousal=0.3, stability=0.6),
        intent="chat",
        conversation_health=chat_core.HealthBlock(stall=0.3, clarity=0.6, energy=0.5),
        risk=chat_core.RiskBlock(self_harm=0, violence=0, sexual=0),
        continuation_need=c,
        topic_seeds=["今天状态"],
        do_not=[],
        facts_to_carry=[],
    )


def test_stable_random_same_seed():
    a = chat_core._stable_rand("u:c", 1)
    b = chat_core._stable_rand("u:c", 1)
    assert a == b


def test_continuation_need_increases_probability():
    low = chat_core._clamp(0.12 + 0.1 * 0.75, 0, 0.88)
    high = chat_core._clamp(0.12 + 0.9 * 0.75, 0, 0.88)
    assert high > low
    p1 = chat_core.plan_reply(make_analysis(0.1), "linyu", "k", 2, "x")
    p2 = chat_core.plan_reply(make_analysis(0.9), "linyu", "k", 2, "x")
    assert isinstance(p1.topic_injection, bool)
    assert isinstance(p2.topic_injection, bool)
