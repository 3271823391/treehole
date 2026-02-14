from core.response_planner import _stable_random, should_inject_topic


def test_stable_random_is_reproducible():
    a = _stable_random("conv-a", 3, salt="fixed")
    b = _stable_random("conv-a", 3, salt="fixed")
    c = _stable_random("conv-a", 4, salt="fixed")
    assert a == b
    assert a != c


def test_inject_probability_respects_threshold():
    conv_key = "conv-prob"
    round_id = 9
    rand = _stable_random(conv_key, round_id)
    inject_low = should_inject_topic(conv_key, round_id, continuation_need=0.0)
    inject_high = should_inject_topic(conv_key, round_id, continuation_need=1.0)
    assert inject_low == (rand < 0.10)
    assert inject_high == (rand < 0.85)
