import unittest

from app.agents.intent_agent import fallback_intent
from app.services.hospital_service import haversine_distance, validate_coordinates
from app.services.medicine_service import extract_medicine_query
from app.services.safety_service import check_emergency


class HealthGenieUnitTests(unittest.TestCase):
    def test_medicine_intent(self):
        self.assertEqual(fallback_intent("Tell me about paracetamol side effects"), "medicine_information")

    def test_combined_intent(self):
        self.assertEqual(
            fallback_intent("Tell me about ibuprofen and find nearby hospitals"),
            "healthcare_search",
        )

    def test_prediction_intent(self):
        self.assertEqual(fallback_intent("Open the kidney prediction form"), "kidney_prediction")

    def test_emergency_guardrail(self):
        self.assertTrue(check_emergency("I have severe chest pain")["emergency_flag"])

    def test_non_emergency(self):
        self.assertFalse(check_emergency("I have a mild headache")["emergency_flag"])

    def test_medicine_query_extraction(self):
        self.assertEqual(extract_medicine_query("Tell me about paracetamol side effects"), "paracetamol")

    def test_distance_zero(self):
        self.assertAlmostEqual(haversine_distance(28.6, 77.2, 28.6, 77.2), 0.0)

    def test_invalid_coordinates(self):
        with self.assertRaises(ValueError):
            validate_coordinates(120, 77)


if __name__ == "__main__":
    unittest.main()
