from core.response_planner import compute_plan
from core.schemas import EmotionAnalysis


def test_planner_calmness_increases_with_anxiety():
    low = EmotionAnalysis(anxiety=0.1, anger=0.1, sadness=0.2)
    high = EmotionAnalysis(anxiety=0.9, anger=0.1, sadness=0.2)
    low_plan = compute_plan(low, {}, None)
    high_plan = compute_plan(high, {}, None)
    assert high_plan.calmness > low_plan.calmness


def test_planner_warmth_and_verbosity_direction():
    sad = EmotionAnalysis(sadness=0.8, anger=0.1, intent="venting")
    angry = EmotionAnalysis(sadness=0.1, anger=0.9, intent="question")
    sad_plan = compute_plan(sad, {}, None)
    angry_plan = compute_plan(angry, {}, None)
    assert sad_plan.warmth > angry_plan.warmth
    assert sad_plan.verbosity >= angry_plan.verbosity
