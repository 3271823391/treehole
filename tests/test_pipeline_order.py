import chat_core


def test_pipeline_order(monkeypatch):
    calls = []

    monkeypatch.setattr(chat_core, "load_user_data", lambda uid: {"system_prompt": "ok", "character_histories": {"history:u:linyu": []}})
    monkeypatch.setattr(chat_core, "save_user_data", lambda uid, data: None)

    def fake_an(*a, **k):
        calls.append("analyzer")
        return chat_core.EmotionAnalysis(
            emotion=chat_core.EmotionBlock(valence=0, arousal=0.2, stability=0.6),
            intent="chat",
            conversation_health=chat_core.HealthBlock(stall=0.5, clarity=0.4, energy=0.5),
            risk=chat_core.RiskBlock(self_harm=0, violence=0, sexual=0),
            continuation_need=0.7,
            topic_seeds=["种子话题"],
            do_not=[],
            facts_to_carry=[],
        )

    def fake_pl(*a, **k):
        calls.append("planner")
        return chat_core.ReplyPlan(
            tone=chat_core.ToneBlock(warmth=0.6, calmness=0.5, firmness=0.5, teasing=0.3),
            initiative=0.5,
            depth=0.5,
            format=chat_core.FormatBlock(min_sentences=2, max_sentences=4, ask_question=True, question_type="open"),
            safety_mode=False,
            topic_injection=True,
            topic_seed="种子话题",
        )

    def fake_draft(system_prompt, history_text, user_input, plan, analysis):
        calls.append("draft")
        assert plan.topic_injection is True
        assert plan.topic_seed == "种子话题"
        return "草稿"

    def fake_rewrite(*a, **k):
        calls.append("rewriter")
        return "重写"

    def fake_guard(*a, **k):
        calls.append("guard")
        return "最终"

    monkeypatch.setattr(chat_core, "analyze_emotion", fake_an)
    monkeypatch.setattr(chat_core, "plan_reply", fake_pl)
    monkeypatch.setattr(chat_core, "generate_draft", fake_draft)
    monkeypatch.setattr(chat_core, "rewrite_voice", fake_rewrite)
    monkeypatch.setattr(chat_core, "post_guard", fake_guard)

    out = "".join(chat_core.stream_chat_with_deepseek("u", "hi", "linyu"))
    assert out == "最终"
    assert calls == ["analyzer", "planner", "draft", "rewriter", "guard"]
