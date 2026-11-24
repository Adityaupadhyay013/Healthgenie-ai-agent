"""MCP client used by deterministic LangGraph service nodes.

MCP_SERVER_URL must be the full Streamable HTTP endpoint, e.g.
https://service.onrender.com/mcp.
"""
import json

from app.config import settings


def _decode_tool_result(result) -> dict:
    if getattr(result, "isError", False):
        raise RuntimeError("MCP tool returned an execution error.")
    structured = getattr(result, "structuredContent", None)
    if structured is None:
        structured = getattr(result, "structured_content", None)
    if isinstance(structured, dict):
        return structured
    texts = [
        item.text for item in (getattr(result, "content", None) or [])
        if getattr(item, "type", None) == "text" and getattr(item, "text", None)
    ]
    if len(texts) == 1:
        try:
            value = json.loads(texts[0])
            if isinstance(value, dict):
                return value
        except json.JSONDecodeError:
            pass
    return {"content": texts}


async def call_mcp_tool(tool_name: str, arguments: dict) -> dict | None:
    """Call a configured remote MCP tool; None means MCP is not configured."""
    if not settings.MCP_SERVER_URL:
        return None
    if not settings.MCP_AUTH_TOKEN:
        raise RuntimeError("MCP_SERVER_URL is set but MCP_AUTH_TOKEN is missing.")

    # This repository pins the MCP Python SDK 1.x API used by FastMCP 2.x.
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    headers = {"Authorization": f"Bearer {settings.MCP_AUTH_TOKEN}"}
    async with streamablehttp_client(
        settings.MCP_SERVER_URL,
        headers=headers,
        timeout=30,
        sse_read_timeout=45,
    ) as (read_stream, write_stream, _get_session_id):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments=arguments)
            return _decode_tool_result(result)
