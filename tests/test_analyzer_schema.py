from core.schemas import EmotionAnalysis


def test_emotion_analysis_accepts_continuation_fields():
    payload = {
        "sentiment": "neutral",
        "intent": "venting",
        "arousal": 0.3,
        "valence": -0.1,
        "anxiety": 0.4,
        "anger": 0.1,
        "sadness": 0.5,
        "risk_self_harm": 0.0,
        "risk_violence": 0.0,
        "risk_abuse": 0.0,
        "continuation_need": 0.72,
        "topic_seeds": ["工作压力", "睡眠状态"],
        "notes": "ok",
    }
    analysis = EmotionAnalysis.model_validate(payload)
    assert analysis.continuation_need == 0.72
    assert analysis.topic_seeds == ["工作压力", "睡眠状态"]
