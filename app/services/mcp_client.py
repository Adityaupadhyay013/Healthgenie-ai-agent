"""Small MCP client used by deterministic LangGraph service nodes.

The MCP endpoint is configured as a complete Streamable HTTP URL, e.g.
https://healthgenie-mcp.onrender.com/mcp.
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

    text_parts = [
        item.text for item in (getattr(result, "content", None) or [])
        if getattr(item, "type", None) == "text" and getattr(item, "text", None)
    ]
    if len(text_parts) == 1:
        try:
            decoded = json.loads(text_parts[0])
            if isinstance(decoded, dict):
                return decoded
        except json.JSONDecodeError:
            pass
    return {"content": text_parts}


async def call_mcp_tool(tool_name: str, arguments: dict) -> dict | None:
    """Call one remote MCP tool; return None only when MCP is not configured."""
    if not settings.MCP_SERVER_URL:
        return None
    if not settings.MCP_AUTH_TOKEN:
        raise RuntimeError("MCP_SERVER_URL is configured but MCP_AUTH_TOKEN is missing.")

    # Keep the MCP SDK import lazy so direct-API fallback still works if MCP is disabled.
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    headers = {"Authorization": f"Bearer {settings.MCP_AUTH_TOKEN}"}
    async with streamablehttp_client(
        settings.MCP_SERVER_URL,
        headers=headers,
        timeout=20,
        sse_read_timeout=30,
    ) as streams:
        read_stream, write_stream = streams[0], streams[1]
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments=arguments)
            return _decode_tool_result(result)
