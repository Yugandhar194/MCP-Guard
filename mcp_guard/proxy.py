from __future__ import annotations

import logging
import os
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import CallToolResult, TextContent, Tool

from .approval import ApprovalBroker
from .config import AppConfig, ServerConfig

log = logging.getLogger("mcp_guard.proxy")


@dataclass
class Upstream:
    config: ServerConfig
    session: ClientSession


async def run_proxy(config: AppConfig, broker: ApprovalBroker) -> None:
    from dataclasses import dataclass

    async with AsyncExitStack() as stack:
        tool_routes: dict[str, tuple[Upstream, str, Tool]] = {}
        for server_config in config.servers:
            params = StdioServerParameters(
                command=server_config.command,
                args=list(server_config.args),
                env={**os.environ, **server_config.env},
            )
            read_stream, write_stream = await stack.enter_async_context(stdio_client(params))
            session = await stack.enter_async_context(ClientSession(read_stream, write_stream))
            await session.initialize()
            upstream = Upstream(server_config, session)
            result = await session.list_tools()
            for tool in result.tools:
                exposed = f"{server_config.name}__{tool.name}"
                if exposed in tool_routes:
                    raise RuntimeError(f"Duplicate exposed tool name: {exposed}")
                tool_routes[exposed] = (upstream, tool.name, tool)
            log.info("Connected upstream '%s' with %d tools", server_config.name, len(result.tools))

        proxy = Server("mcp-guard")

        @proxy.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name=exposed,
                    description=f"[Approval required] {tool.description or ''}".strip(),
                    inputSchema=tool.inputSchema,
                )
                for exposed, (_, _, tool) in tool_routes.items()
            ]

        @proxy.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any] | None) -> CallToolResult:
            route = tool_routes.get(name)
            if route is None:
                return CallToolResult(
                    isError=True,
                    content=[TextContent(type="text", text=f"Unknown tool: {name}")],
                )
            upstream, original_name, _ = route
            args = arguments or {}
            log.info("Approval requested for %s", name)
            allowed = await broker.request_approval(
                upstream.config.name, original_name, args
            )
            if not allowed:
                log.info("Blocked tool call %s", name)
                return CallToolResult(
                    isError=True,
                    content=[TextContent(
                        type="text",
                        text="Blocked by MCP-Guard: user denied or approval timed out.",
                    )],
                )
            try:
                log.info("Forwarding approved tool call %s", name)
                return await upstream.session.call_tool(original_name, args)
            except Exception as exc:
                log.exception("Upstream tool call failed: %s", name)
                return CallToolResult(
                    isError=True,
                    content=[TextContent(
                        type="text",
                        text=f"Upstream call failed: {type(exc).__name__}: {exc}",
                    )],
                )

        log.info("MCP-Guard ready; exposing %d tools", len(tool_routes))
        read_stream, write_stream = await stack.enter_async_context(stdio_server())
        await proxy.run(read_stream, write_stream, proxy.create_initialization_options())
