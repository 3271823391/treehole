from pathlib import Path

from fastapi.testclient import TestClient

import data_store
from core.schemas import EmotionAnalysis
from main import app

UID_A = "u_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
UID_B = "u_bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"


def _init_temp_store(monkeypatch, tmp_path: Path):
    db = tmp_path / "user_data.json"
    db.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(data_store, "USER_DATA_FILE", str(db))


def test_chat_stream_pipeline_and_state(monkeypatch, tmp_path):
    _init_temp_store(monkeypatch, tmp_path)

    monkeypatch.setattr("routers.chat.analyze_emotion", lambda history, text: EmotionAnalysis(intent="venting", anxiety=0.8, summary="stress"))

    def fake_stream(messages):
        yield "你"
        yield "好"

    monkeypatch.setattr("routers.chat.llm_stream", fake_stream)

    client = TestClient(app)
    payload = {"user_id": UID_A, "user_input": "我今天很焦虑", "character_id": "linyu", "device_id": "d1"}
    resp = client.post("/chat_stream", json=payload)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/plain")
    assert resp.text == "你好"

    stored = data_store.load_user_data(UID_A)
    conv_key = f"{UID_A}:d1:linyu"
    turn = stored["conv_states"][conv_key]["turns"][0]
    assert turn["analysis"]["summary"] == "stress"
    assert turn["plan"]["calmness"] > 0.6
    assert turn["assistant_text"].startswith("你好")


def test_chat_stream_conv_key_isolation(monkeypatch, tmp_path):
    _init_temp_store(monkeypatch, tmp_path)
    monkeypatch.setattr("routers.chat.analyze_emotion", lambda history, text: EmotionAnalysis(intent="venting", summary="ok"))
    monkeypatch.setattr("routers.chat.llm_stream", lambda messages: iter(["A"]))

    client = TestClient(app)
    client.post("/chat_stream", json={"user_id": UID_B, "user_input": "x", "character_id": "linyu", "device_id": "d1"})
    client.post("/chat_stream", json={"user_id": UID_B, "user_input": "y", "character_id": "suwan", "device_id": "d2"})

    stored = data_store.load_user_data(UID_B)
    keys = set(stored.get("conv_states", {}).keys())
    assert f"{UID_B}:d1:linyu" in keys
    assert f"{UID_B}:d2:suwan" in keys
    assert stored["conv_states"][f"{UID_B}:d1:linyu"]["turns"][0]["user_text"] == "x"
    assert stored["conv_states"][f"{UID_B}:d2:suwan"]["turns"][0]["user_text"] == "y"
