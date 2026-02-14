import chat_core
from fastapi.testclient import TestClient

from main import app


def _analysis(valence: float = 0.0, stall: float = 0.6, self_harm: float = 0.0):
    return chat_core.EmotionAnalysis(
        emotion=chat_core.EmotionBlock(valence=valence, arousal=0.3, stability=0.6),
        intent="chat",
        conversation_health=chat_core.HealthBlock(stall=stall, clarity=0.6, energy=0.5),
        risk=chat_core.RiskBlock(self_harm=self_harm, violence=0, sexual=0),
        continuation_need=0.7,
        topic_seeds=["今天状态"],
        do_not=[],
        facts_to_carry=[],
    )


def test_roles_not_inverted(monkeypatch):
    seen = {}

    def fake_json_call(messages, temperature=0):
        if any(m.get("content", "").startswith("CONTROL=") for m in messages):
            seen["messages"] = messages
            return "收到，你想先说哪一块？"
        return "{}"

    plan = chat_core.ReplyPlan(
        tone=chat_core.ToneBlock(warmth=0.5, calmness=0.5, firmness=0.5, teasing=0.2),
        initiative=0.5,
        depth=0.5,
        format=chat_core.FormatBlock(min_sentences=2, max_sentences=4, ask_question=True, question_type="open"),
        safety_mode=False,
        topic_injection=False,
        topic_seed="今天状态",
    )

    monkeypatch.setattr(chat_core, "_json_call", fake_json_call)
    history = [{"role": "assistant", "content": "你呢？"}]
    chat_core.generate_draft("你是助手", history, "我不太好", plan, _analysis())

    messages = seen["messages"]
    assert messages[-1]["role"] == "user"
    assert messages[-1]["content"] == "我不太好"


def test_negative_user_no_self_disclosure():
    final_text = chat_core.post_guard("我最近状态很差。", False, "我不太好")
    assert not final_text.startswith("我最近")
    assert final_text.startswith("你")


def test_topic_injection_gated_on_negative_valence():
    plan = chat_core.plan_reply(_analysis(valence=-0.5, stall=0.9), "linyu", "u:linyu", 1, "聊聊")
    assert plan.topic_injection is False


def test_history_api_untouched():
    client = TestClient(app)
    resp = client.get('/load_history', params={'user_id': 'u_40bd001563085fc35165329ea1ff5c5ecbdbbeef', 'character_id': 'linyu'})
    assert resp.status_code == 200
    data = resp.json()
    assert list(data.keys()) == ["ok", "history"]
    assert isinstance(data["history"], list)
    if data["history"]:
        row = data["history"][0]
        assert "role" in row
        assert "content" in row
