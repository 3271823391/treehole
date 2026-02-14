from fastapi.testclient import TestClient

from main import app


def test_history_shape_unchanged():
    client = TestClient(app)
    resp = client.get('/load_history', params={'user_id': 'u_40bd001563085fc35165329ea1ff5c5ecbdbbeef', 'character_id': 'linyu'})
    assert resp.status_code == 200
    data = resp.json()
    assert set(data.keys()) == {"ok", "history"}
    assert isinstance(data["ok"], bool)
    assert isinstance(data["history"], list)
    if data["history"]:
        row = data["history"][0]
        assert "role" in row
        assert "content" in row
