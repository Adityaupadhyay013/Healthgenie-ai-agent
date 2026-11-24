import os
import unittest

os.environ.setdefault("MCP_AUTH_TOKEN", "healthgenie-test-token")

from fastmcp import Client
from fastapi.testclient import TestClient
from mcp_server import app, mcp


class MCPServerTests(unittest.IsolatedAsyncioTestCase):
    async def test_server_exposes_expected_read_only_tools(self):
        async with Client(mcp) as client:
            tools = await client.list_tools()
        names = {tool.name for tool in tools}
        self.assertIn("search_medicine_reference", names)
        self.assertIn("find_nearby_health_facilities", names)

    def test_health_route_is_public(self):
        with TestClient(app) as client:
            response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")

    def test_mcp_route_rejects_missing_bearer_token(self):
        with TestClient(app) as client:
            response = client.post("/mcp", json={})
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
