import pytest

from core.emotion_analyzer import EmotionAnalyzeError, analyze_emotion


def test_analyzer_retries_and_succeeds(monkeypatch):
    calls = {"n": 0}

    def fake_complete(messages, temperature=0.0):
        calls["n"] += 1
        if calls["n"] == 1:
            return "not json"
        return '{"sentiment":"neutral","intent":"venting","arousal":0.2,"valence":0,"anxiety":0.1,"anger":0,"sadness":0.2,"risk_self_harm":0,"risk_violence":0,"risk_abuse":0,"notes":"ok"}'

    monkeypatch.setattr("core.emotion_analyzer.llm_complete", fake_complete)
    analysis = analyze_emotion("h", "u")
    assert analysis.intent == "venting"
    assert calls["n"] == 2


def test_analyzer_retries_then_fails(monkeypatch):
    def fake_complete(messages, temperature=0.0):
        return "still bad"

    monkeypatch.setattr("core.emotion_analyzer.llm_complete", fake_complete)
    with pytest.raises(EmotionAnalyzeError):
        analyze_emotion("h", "u")
