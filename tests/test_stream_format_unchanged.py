from fastapi.testclient import TestClient

import chat_core
from main import app


def test_stream_protocol_plaintext(monkeypatch):
    monkeypatch.setattr(chat_core, "stream_chat_with_deepseek", lambda *a, **k: iter(["你好", "世界"]))
    client = TestClient(app)
    resp = client.post('/chat_stream', json={"user_id": "u_40bd001563085fc35165329ea1ff5c5ecbdbbeef", "user_input": "hi", "character_id": "linyu"})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/plain")
    first = resp.text[:8]
    assert "data:" not in first
