import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_legacy_login_route_redirects_to_intro_page():
    response = client.get('/routers/login.html', follow_redirects=False)

    assert response.status_code == 307
    assert response.headers['location'] == '/'
