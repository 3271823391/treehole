import pytest

from core.emotion_analyzer import EmotionAnalyzerError, analyze_emotion


def test_analyzer_retries_once(monkeypatch):
    calls = {"n": 0}

    def fake_complete(messages, temperature=0.0):
        calls["n"] += 1
        if calls["n"] == 1:
            return "not json"
        return '{"intent":"venting","valence":0.1,"arousal":0.2,"anxiety":0.2,"anger":0.1,"sadness":0.3,"risk_self_harm":0.0,"risk_violence":0.0,"summary":"ok"}'

    monkeypatch.setattr("core.emotion_analyzer.llm_complete", fake_complete)
    result = analyze_emotion("h", "u")
    assert result.intent == "venting"
    assert calls["n"] == 2


def test_analyzer_raises_after_retry(monkeypatch):
    monkeypatch.setattr("core.emotion_analyzer.llm_complete", lambda *args, **kwargs: "bad")
    with pytest.raises(EmotionAnalyzerError):
        analyze_emotion("h", "u")
