"""MCP client used by deterministic LangGraph service nodes.

MCP_SERVER_URL must be the full Streamable HTTP endpoint, e.g. https://service.onrender.com/mcp.
When unset, local development uses the same direct source adapters.
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

    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client
    import httpx

    timeout = httpx.Timeout(30.0, connect=10.0, read=45.0)
    async with httpx.AsyncClient(
        headers={"Authorization": f"Bearer {settings.MCP_AUTH_TOKEN}"},
        timeout=timeout,
    ) as http_client:
        async with streamable_http_client(
            settings.MCP_SERVER_URL,
            http_client=http_client,
        ) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments=arguments)
                return _decode_tool_result(result)
