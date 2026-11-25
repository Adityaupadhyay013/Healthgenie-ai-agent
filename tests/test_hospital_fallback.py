import unittest
from unittest.mock import AsyncMock, patch

from app.services import hospital_service


class HospitalFallbackTests(unittest.IsolatedAsyncioTestCase):
    async def test_mcp_failure_falls_back_to_direct_provider(self):
        expected = [{"name": "Example Hospital", "latitude": 28.6, "longitude": 77.2}]
        with patch(
            "app.services.mcp_client.call_mcp_tool",
            new=AsyncMock(side_effect=RuntimeError("MCP unavailable")),
        ), patch(
            "app.services.hospital_service.find_nearby_hospitals_direct",
            new=AsyncMock(return_value=expected),
        ) as direct:
            result = await hospital_service.find_nearby_hospitals(28.6, 77.2)

        self.assertEqual(result, expected)
        direct.assert_awaited_once_with(28.6, 77.2)

    async def test_empty_mcp_result_falls_back_to_direct_provider(self):
        expected = [{"name": "Nearby Clinic"}]
        with patch(
            "app.services.mcp_client.call_mcp_tool",
            new=AsyncMock(return_value={"facilities": []}),
        ), patch(
            "app.services.hospital_service.find_nearby_hospitals_direct",
            new=AsyncMock(return_value=expected),
        ) as direct:
            result = await hospital_service.find_nearby_hospitals(10.0, 20.0)

        self.assertEqual(result, expected)
        direct.assert_awaited_once_with(10.0, 20.0)

    def test_overpass_endpoints_include_configured_and_fallbacks(self):
        with patch.object(hospital_service.settings, "OVERPASS_URL", "https://custom.example/api"):
            endpoints = hospital_service._overpass_endpoints()

        self.assertEqual(endpoints[0], "https://custom.example/api")
        self.assertIn("https://overpass-api.de/api/interpreter", endpoints)
        self.assertIn("https://overpass.kumi.systems/api/interpreter", endpoints)
        self.assertEqual(len(endpoints), len(set(endpoints)))


if __name__ == "__main__":
    unittest.main()
