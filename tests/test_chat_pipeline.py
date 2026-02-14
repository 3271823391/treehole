import json
from pathlib import Path

from fastapi.testclient import TestClient


def _setup_store(monkeypatch, tmp_path):
    store = tmp_path / "user_data.json"
    store.write_text("{}", encoding="utf-8")
    monkeypatch.setattr("data_store.USER_DATA_FILE", str(store))
    return store


def _seed_user(store: Path, user_id: str):
    data = {
        user_id: {
            "plan": "plus",
            "system_prompt": "你是一个温柔的倾听者",
            "memories": [],
            "history": [],
            "has_greeted": False,
            "chat_count": 0,
            "relationships": {},
            "profile": {"display_name": "", "avatar_url": "", "password_hash": ""},
        }
    }
    store.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def test_chat_stream_pipeline_and_state(monkeypatch, tmp_path):
    store = _setup_store(monkeypatch, tmp_path)
    _seed_user(store, "u_1111111111111111111111111111111111111111")

    from main import app
    from core.schemas import EmotionAnalysis

    monkeypatch.setattr(
        "routers.chat.analyze_emotion",
        lambda history, text: EmotionAnalysis(intent="venting", anxiety=0.7, valence=-0.4),
    )
    monkeypatch.setattr("routers.chat.llm_stream", lambda messages: iter(["你", "好", "。", "我", "在", "。"]))

    client = TestClient(app)
    with client.stream("POST", "/chat_stream", json={"user_id": "u_1111111111111111111111111111111111111111", "user_input": "我很焦虑", "character_id": "linyu"}) as resp:
        text = "".join(resp.iter_text())

    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/plain")
    assert "你" in text

    saved = json.loads(store.read_text(encoding="utf-8"))
    states = saved["u_1111111111111111111111111111111111111111"]["conversation_states"]
    conv_state = states["u_1111111111111111111111111111111111111111:default:linyu"]
    turn = conv_state["turns"][0]
    assert turn["analysis"]["intent"] == "venting"
    assert turn["assistant_text"]
    assert "plan" in turn


def test_chat_stream_isolated_conv_keys(monkeypatch, tmp_path):
    store = _setup_store(monkeypatch, tmp_path)
    _seed_user(store, "u_2222222222222222222222222222222222222222")

    from main import app
    from core.schemas import EmotionAnalysis

    monkeypatch.setattr("routers.chat.analyze_emotion", lambda history, text: EmotionAnalysis(intent="qa"))
    monkeypatch.setattr("routers.chat.llm_stream", lambda messages: iter(["ok", "。", "done", "。"]))

    client = TestClient(app)
    with client.stream("POST", "/chat_stream", json={"user_id": "u_2222222222222222222222222222222222222222", "user_input": "A", "character_id": "linyu", "device_id": "d1"}) as _:
        pass
    with client.stream("POST", "/chat_stream", json={"user_id": "u_2222222222222222222222222222222222222222", "user_input": "B", "character_id": "suwan", "device_id": "d2"}) as _:
        pass

    saved = json.loads(store.read_text(encoding="utf-8"))
    states = saved["u_2222222222222222222222222222222222222222"]["conversation_states"]
    assert "u_2222222222222222222222222222222222222222:d1:linyu" in states
    assert "u_2222222222222222222222222222222222222222:d2:suwan" in states
    assert states["u_2222222222222222222222222222222222222222:d1:linyu"]["turns"][0]["user_text"] == "A"
    assert states["u_2222222222222222222222222222222222222222:d2:suwan"]["turns"][0]["user_text"] == "B"
