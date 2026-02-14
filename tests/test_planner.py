from core.response_planner import compute_plan
from core.schemas import EmotionAnalysis


def test_planner_high_anxiety_increases_calmness_and_warmth():
    analysis = EmotionAnalysis(anxiety=0.9, sadness=0.6, valence=-0.7)
    plan = compute_plan(analysis)
    assert plan.calmness > 0.7
    assert plan.warmth > 0.7


def test_planner_high_anger_reduces_verbosity_and_increases_firmness():
    analysis = EmotionAnalysis(anger=0.9)
    plan = compute_plan(analysis)
    assert plan.firmness > 0.45
    assert plan.verbosity < 0.4
