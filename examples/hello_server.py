"""Tiny, harmless upstream MCP server for trying MCP-Guard locally."""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("mcp-guard-demo")


@mcp.tool()
def echo(message: str) -> str:
    """Return the supplied message. Safe for testing approval and blocking."""
    return f"Echo from the upstream server: {message}"


@mcp.tool()
def add_numbers(a: int, b: int) -> int:
    """Add two integers. Safe for testing tool-call approval."""
    return a + b


if __name__ == "__main__":
    mcp.run(transport="stdio")
