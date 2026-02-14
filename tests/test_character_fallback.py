import json

from fastapi.testclient import TestClient


def test_treehole_referer_fallback_character_id(monkeypatch, tmp_path):
    store = tmp_path / "user_data.json"
    user_id = "u_6666666666666666666666666666666666666666"
    store.write_text(
        json.dumps(
            {
                user_id: {
                    "plan": "plus",
                    "system_prompt": "你是一个温柔的倾听者",
                    "memories": [],
                    "history": [],
                    "has_greeted": False,
                    "chat_count": 0,
                    "profile": {"display_name": "", "avatar_url": "", "password_hash": ""},
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("data_store.USER_DATA_FILE", str(store))

    from main import app
    from core.schemas import EmotionAnalysis

    monkeypatch.setattr("routers.chat.analyze_emotion", lambda history, text: EmotionAnalysis(intent="qa"))
    monkeypatch.setattr("routers.chat.llm_stream", lambda messages: iter(["ok"]))

    client = TestClient(app)
    with client.stream(
        "POST",
        "/chat_stream",
        headers={"referer": "http://testserver/treehole_plus"},
        json={"user_id": user_id, "user_input": "hi", "device_id": "d-fallback"},
    ) as resp:
        _ = "".join(resp.iter_text())

    assert resp.status_code == 200

    saved = json.loads(store.read_text(encoding="utf-8"))
    states = saved[user_id]["conversation_states"]
    assert f"{user_id}:d-fallback:treehole" in states
