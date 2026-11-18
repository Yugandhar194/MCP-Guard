from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ServerConfig:
    name: str
    command: str
    args: tuple[str, ...]
    env: dict[str, str]


@dataclass(frozen=True)
class AppConfig:
    approval_timeout_seconds: int
    servers: tuple[ServerConfig, ...]


def load_config(path: Path) -> AppConfig:
    if not path.is_file():
        raise FileNotFoundError(
            f"Config not found: {path}. Copy config/servers.example.json to config/servers.json."
        )
    raw = json.loads(path.read_text(encoding="utf-8"))
    timeout = int(raw.get("approval_timeout_seconds", 180))
    if timeout < 1:
        raise ValueError("approval_timeout_seconds must be at least 1")

    servers: list[ServerConfig] = []
    names: set[str] = set()
    for item in raw.get("servers", []):
        name = str(item["name"]).strip()
        command = str(item["command"]).strip()
        if not name or not command:
            raise ValueError("Every server needs a non-empty name and command")
        if "__" in name:
            raise ValueError("Server names cannot contain '__'")
        if name in names:
            raise ValueError(f"Duplicate upstream server name: {name}")
        names.add(name)
        servers.append(ServerConfig(
            name=name,
            command=command,
            args=tuple(str(v) for v in item.get("args", [])),
            env={str(k): str(v) for k, v in item.get("env", {}).items()},
        ))
    if not servers:
        raise ValueError("No upstream MCP servers configured. Add at least one server.")
    return AppConfig(timeout, tuple(servers))
