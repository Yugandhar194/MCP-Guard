import json

import pytest

from mcp_guard.config import load_config


def test_load_config(tmp_path):
    path = tmp_path / "servers.json"
    path.write_text(json.dumps({
        "approval_timeout_seconds": 45,
        "servers": [{
            "name": "files",
            "command": "python",
            "args": ["server.py"],
            "env": {"FLAG": "1"},
        }],
    }))
    config = load_config(path)
    assert config.approval_timeout_seconds == 45
    assert config.servers[0].name == "files"
    assert config.servers[0].args == ("server.py",)


def test_requires_server(tmp_path):
    path = tmp_path / "servers.json"
    path.write_text('{"servers": []}')
    with pytest.raises(ValueError, match="No upstream"):
        load_config(path)


def test_rejects_duplicate_names(tmp_path):
    path = tmp_path / "servers.json"
    path.write_text(json.dumps({"servers": [
        {"name": "same", "command": "python"},
        {"name": "same", "command": "python"},
    ]}))
    with pytest.raises(ValueError, match="Duplicate"):
        load_config(path)
