import json
import threading
import urllib.error
import urllib.request
from http.server import HTTPServer

import pytest

from app.server import Handler


@pytest.fixture
def base_url():
    server = HTTPServer(("127.0.0.1", 0), Handler)       # port 0 = pick a free port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


def test_health(base_url):
    with urllib.request.urlopen(f"{base_url}/health", timeout=5) as resp:
        assert resp.status == 200
        assert json.loads(resp.read())["status"] == "ok"


def test_unknown_path_is_404(base_url):
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(f"{base_url}/nope", timeout=5)
    assert exc.value.code == 404
