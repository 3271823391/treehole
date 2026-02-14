import json

from fastapi.testclient import TestClient


def test_history_treehole_key_consistency(monkeypatch, tmp_path):
    store = tmp_path / "user_data.json"
    user_id = "u_5555555555555555555555555555555555555555"
    device_id = "TREEHOLE_DEVICE_ID_TEST"
    conv_key = f"{user_id}:{device_id}:treehole"
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
                    "conversation_states": {
                        conv_key: {
                            "conv_key": conv_key,
                            "user_id": user_id,
                            "device_id": device_id,
                            "character_id": "treehole",
                            "round_seq": 2,
                            "summary": "",
                            "turns": [
                                {
                                    "round_id": 1,
                                    "user_text": "第一句",
                                    "assistant_text": "第一回",
                                    "analysis": {"sentiment": "neutral", "intent": "venting"},
                                    "plan": {},
                                    "error": "",
                                    "created_at": 1.0,
                                },
                                {
                                    "round_id": 2,
                                    "user_text": "第二句",
                                    "assistant_text": "第二回",
                                    "analysis": {"sentiment": "neutral", "intent": "venting"},
                                    "plan": {},
                                    "error": "",
                                    "created_at": 2.0,
                                },
                            ],
                            "last_plan": None,
                        }
                    },
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("data_store.USER_DATA_FILE", str(store))

    from main import app

    client = TestClient(app)
    resp = client.get(
        "/api/chat/history",
        params={"user_id": user_id, "character_id": "treehole", "device_id": device_id, "limit": 50},
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["ok"] is True
    assert payload["messages"] == [
        {"role": "user", "content": "第一句"},
        {"role": "assistant", "content": "第一回"},
        {"role": "user", "content": "第二句"},
        {"role": "assistant", "content": "第二回"},
    ]
