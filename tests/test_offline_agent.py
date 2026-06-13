import unittest

from synthetic.patient_generator import generate_patient
from agent.foundry_agent import get_agent


class TestOfflineVaccineGenicsAgent(unittest.TestCase):
    def test_offline_agent_structured_output(self):
        patient = generate_patient(1)
        agent = get_agent(offline=True)
        result = agent.analyze_patient(patient.to_dict())

        self.assertIn("full_report", result)
        self.assertIn("structured_report", result)
        self.assertIn("platform", result["structured_report"])
        self.assertIn("protection_probability", result["structured_report"])
        self.assertIn("recommendation", result["structured_report"])
        self.assertTrue(result["full_report"].count("--- JSON SUMMARY ---") == 1)
        self.assertIsInstance(result["structured_report"]["risk_flags"], list)
        self.assertIn(result["platform"], {"mRNA", "adenoviral_vector", "protein_subunit"})


if __name__ == "__main__":
    unittest.main()
