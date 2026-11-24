"""Smoke-test the deployed HealthGenie MCP endpoint.

Set MCP_SERVER_URL and MCP_AUTH_TOKEN, then run:
    python scripts/check_mcp_connection.py
"""
import asyncio
import os

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main():
    url = os.environ["MCP_SERVER_URL"]
    token = os.environ["MCP_AUTH_TOKEN"]
    headers = {"Authorization": f"Bearer {token}"}

    async with streamablehttp_client(
        url,
        headers=headers,
        timeout=30,
        sse_read_timeout=45,
    ) as (read_stream, write_stream, _get_session_id):
        async with ClientSession(read_stream, write_stream) as session:
            initialized = await session.initialize()
            tools = await session.list_tools()
            print(f"Connected to MCP server: {initialized.serverInfo.name}")
            print("Available tools:")
            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description or ''}")


if __name__ == "__main__":
    asyncio.run(main())
