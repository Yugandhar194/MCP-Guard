# MCP-Guard

A local human-approval gateway for Model Context Protocol (MCP) tool calls.

MCP-Guard sits between an MCP host and configured upstream MCP servers. It discovers upstream tools, displays each invocation in a desktop approval window, and forwards only approved calls.

> **Scope:** MCP-Guard governs only traffic explicitly routed through it. Claude Desktop can use it as a local stdio MCP server. Claude Web/cloud integrations are not automatically intercepted by a local desktop process; they require a supported remote MCP endpoint that routes calls through an MCP-Guard deployment.

## Features

- Per-call **Allow once** / **Block** decisions.
- Requests remain pending until a decision or timeout.
- Concurrent pending approvals with independent request IDs.
- Displays upstream, tool, arguments, and request ID.
- Fail-closed timeout and upstream error handling.
- Multiple upstream stdio MCP servers.
- JSON configuration and rotating logs.
- Full argument payloads are not written to logs.

## Requirements

- Python 3.11+
- Desktop environment for the approval window
- Upstream MCP servers installed and runnable locally
- Claude Desktop or another stdio-capable MCP host

## Install

```bash
git clone https://github.com/Yugandhar194/MCP-Guard.git
cd MCP-Guard
python -m venv .venv
```

Activate the environment:

```bash
# Windows
.venv\\Scripts\\activate

# macOS / Linux
source .venv/bin/activate
```

Install dependencies and create your local config:

```bash
pip install -e .
cp config/servers.example.json config/servers.json
```

Edit `config/servers.json` with the command and arguments for each trusted upstream MCP server.

## Run

```bash
python -m mcp_guard --config config/servers.json
```

Keep MCP-Guard running while your MCP host is connected.

## Claude Desktop

Back up your Claude Desktop configuration, then add an entry similar to this. Replace paths with absolute paths for your machine:

```json
{
  "mcpServers": {
    "mcp-guard": {
      "command": "/absolute/path/to/MCP-Guard/.venv/bin/python",
      "args": [
        "-m", "mcp_guard",
        "--config", "/absolute/path/to/MCP-Guard/config/servers.json"
      ]
    }
  }
}
```

On Windows, use the virtual environment's `python.exe` path. Restart Claude Desktop after editing the configuration.

Configure the actual MCP servers inside MCP-Guard's `servers.json`. If you also configure those servers directly in Claude Desktop, those direct connections bypass approval.

## Configuration

See [config/servers.example.json](config/servers.example.json). Each server entry has a unique name, executable command, argument list, and optional environment variables. Tools are exposed as `server__tool`. For example, `filesystem/read_file` becomes `filesystem__read_file`.

## Approval flow

1. MCP-Guard starts configured upstream stdio servers and discovers their tools.
2. The host invokes a namespaced tool.
3. MCP-Guard creates a pending approval and waits.
4. The desktop window shows the invocation and arguments.
5. **Allow once** forwards the original call. **Block** returns an error without invoking upstream.
6. If no decision is made before the configured timeout, the call is blocked.

## Security notes

- Review upstream commands and environment variables before enabling them.
- Arguments may contain secrets or personal data. They are displayed locally but omitted from application logs.
- Keep configuration private if it contains credentials.
- MCP-Guard is an approval boundary, not a sandbox. An approved tool retains all permissions of its upstream server.
- Use least-privilege credentials and trusted MCP servers.

## Demo video

A demo video has not been recorded or uploaded yet. See [demo/README.md](demo/README.md) for a short recording script covering an allowed call, a blocked call, and concurrent requests. Record with test data and attach the video to a GitHub Release.

## Development

```bash
pip install -e .[dev]
pytest -q
```

See [docs/architecture.md](docs/architecture.md) for the runtime design.

## Current limitations

- This release supports upstream stdio MCP servers; remote HTTP transports are not included.
- Tool names are namespaced as `server__tool`.
- Interactive approval requires a graphical desktop session.
- Claude Web is covered only if its integration routes calls through this gateway.

## License

MIT. See [LICENSE](LICENSE).
