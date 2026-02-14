import json

from fastapi.testclient import TestClient


def test_chat_stream_treehole_character_is_accepted(monkeypatch, tmp_path):
    store = tmp_path / "user_data.json"
    user_id = "u_4444444444444444444444444444444444444444"
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
    monkeypatch.setattr("routers.chat.llm_stream", lambda messages: iter(["好", "的"] ))

    client = TestClient(app)
    with client.stream(
        "POST",
        "/chat_stream",
        json={"user_id": user_id, "user_input": "你好", "character_id": "treehole", "device_id": "d-tree"},
    ) as resp:
        body = "".join(resp.iter_text())

    assert resp.status_code != 400
    assert "invalid_character_id" not in body
