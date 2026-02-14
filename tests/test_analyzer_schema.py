import chat_core


def test_analyzer_schema(monkeypatch):
    sample = '{"emotion":{"valence":0.1,"arousal":0.4,"stability":0.7},"intent":"chat","conversation_health":{"stall":0.2,"clarity":0.7,"energy":0.5},"risk":{"self_harm":0,"violence":0,"sexual":0},"continuation_need":0.6,"topic_seeds":["今天心情","最近睡眠"],"do_not":["不要套话"],"facts_to_carry":["用户在加班"]}'
    monkeypatch.setattr(chat_core, "_json_call", lambda *a, **k: sample)
    out = chat_core.analyze_emotion("", "你好")
    assert out.continuation_need == 0.6
    assert out.topic_seeds
    assert out.do_not
    assert out.facts_to_carry
