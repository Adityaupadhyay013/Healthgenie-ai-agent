import unittest

from app.agents.intent_agent import fallback_intent
from app.services.hospital_service import haversine_distance, validate_coordinates
from app.services.medicine_service import extract_medicine_query
from app.services.safety_service import check_emergency


class HealthGenieUnitTests(unittest.TestCase):
    def test_medicine_intent(self):
        self.assertEqual(fallback_intent("Tell me about paracetamol side effects"), "medicine_information")

    def test_hospital_only_query_does_not_trigger_medicine_lookup(self):
        self.assertEqual(fallback_intent("Suggest me some hospitals near me"), "hospital_search")

    def test_hospital_query_with_older_medicine_context_stays_hospital_only(self):
        self.assertEqual(fallback_intent("Find hospitals near me"), "hospital_search")

    def test_explicit_combined_query(self):
        self.assertEqual(
            fallback_intent("Tell me about ibuprofen side effects and find nearby hospitals"),
            "healthcare_search",
        )

    def test_symptom_medicine_request(self):
        self.assertEqual(fallback_intent("Suggest me some medicines for fever"), "general_health")
        self.assertEqual(fallback_intent("Suggest a medicine for nausea"), "general_health")
        self.assertEqual(fallback_intent("Recommend medicine for headache"), "general_health")

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
