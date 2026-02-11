import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_intro_page_logout_clears_user_id_and_redirects_to_logout_flag():
    response = client.get('/')

    assert response.status_code == 200
    html = response.text
    assert "const STORAGE_USER_ID_KEY = 'treehole_user_id';" in html
    assert 'localStorage.removeItem(STORAGE_USER_ID_KEY);' in html
    assert "window.location.assign('/?logout=1');" in html
