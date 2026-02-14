import json

from fastapi.testclient import TestClient


def test_history_api_returns_messages_in_order(monkeypatch, tmp_path):
    store = tmp_path / "user_data.json"
    user_id = "u_3333333333333333333333333333333333333333"
    conv_key = f"{user_id}:default:linyu"
    data = {
        user_id: {
            "plan": "plus",
            "system_prompt": "你是一个温柔的倾听者",
            "memories": [],
            "history": [],
            "has_greeted": False,
            "chat_count": 0,
            "character_histories": {},
            "profile": {"display_name": "", "avatar_url": "", "password_hash": ""},
            "conversation_states": {
                conv_key: {
                    "conv_key": conv_key,
                    "user_id": user_id,
                    "device_id": "default",
                    "character_id": "linyu",
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
    }
    store.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr("data_store.USER_DATA_FILE", str(store))

    from main import app

    client = TestClient(app)
    resp = client.get(
        "/api/chat/history",
        params={"user_id": user_id, "character_id": "linyu", "device_id": "default", "limit": 50},
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
