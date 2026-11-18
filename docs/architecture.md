# Architecture

    MCP host (Claude Desktop / compatible host)
                       |
                 stdio MCP
                       |
                 MCP-Guard
                       |
              configured upstreams
                       |
              ApprovalBroker
                       |
                Qt desktop UI
                  /       \
               Allow     Block
                 |         |
          upstream call  MCP error

## Runtime

- The proxy and upstream ClientSession objects run on an asyncio event-loop thread.
- The Qt approval window runs on the main GUI thread.
- ApprovalBroker is the thread-safe boundary between those threads.
- Each invocation receives an independent request ID and decision future.
- Approval waits are bounded by approval_timeout_seconds. Timeout fails closed.

## Tool routing

At startup, MCP-Guard starts configured upstream stdio servers, initializes a client session for each, and retrieves its tool list. Tools are exposed using server__tool names. Calls are routed to the matching upstream session and original tool name.

## Trust boundaries

Only calls routed through MCP-Guard are governed. It does not inspect unrelated network traffic or direct MCP connections. Approved calls are forwarded with their arguments unchanged. This is not a sandbox.

## Failure handling

- Invalid or missing configuration stops startup.
- Upstream startup and initialization failures stop startup.
- Unknown tools return an error.
- Denial and timeout do not invoke upstream.
- Upstream call exceptions become MCP tool errors.
- Full argument payloads are not logged.
