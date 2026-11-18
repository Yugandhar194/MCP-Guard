# Demo recording guide

A demo video has not been recorded or uploaded yet. Use this script to capture a short desktop walkthrough after installing and configuring MCP-Guard.

## Suggested 2-3 minute walkthrough

1. Start MCP-Guard and show the empty approval window.
2. Connect Claude Desktop to the configured mcp-guard server.
3. Ask Claude to invoke a harmless read-only upstream tool.
4. Show the pending request, including server, tool, arguments, and request ID.
5. Click Allow once and show the upstream result returned to Claude.
6. Invoke another harmless tool and click Block. Show the blocked tool result.
7. Trigger two calls close together and show both pending approvals independently.
8. Explain that unanswered requests time out and are blocked.

## Recording checklist

- Use test data only; hide credentials, tokens, personal information, and private paths.
- Demonstrate a harmless tool, never a destructive operation.
- Add captions or a brief voiceover.
- Upload the recording to a GitHub Release and link it here.
