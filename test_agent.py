"""Quick test of the offline agent chain-of-thought."""
import sys
sys.path.insert(0, ".")

from src.synthetic.patient_generator import generate_cohort
from src.pharmacogenomics.risk_calculator import analyze_patient
from src.agent.foundry_agent import get_agent

cohort = generate_cohort(5, seed=42)
p = cohort[0]

report = analyze_patient(p.patient_id, p.age, p.sex, p.variants, p.hla_haplotype, p.apoe_genotype, "mRNA")

patient_data = p.to_dict()
patient_data["module_scores"] = {
    "tlr": {"score": report.tlr.score},
    "hla": {"score": report.hla.score},
    "stat": {"score": report.stat.score},
    "apoe_peg3": {"score": report.apoe.score},
}
patient_data["irt"] = {
    "theta": report.irt.theta,
    "probability_protection": report.irt.probability_protection,
    "confidence_interval": report.irt.confidence_interval,
    "seroconversion_likely": report.irt.seroconversion_likely,
    "dose_recommendation": report.irt.dose_recommendation,
}

agent = get_agent(offline=True)
result = agent.analyze_patient(patient_data)
print(result["full_report"])
print()
print("REASONING TRACE:")
for step in result["reasoning_trace"]:
    print(f"  [{step['step']}] {step['tool']}: {step['output']}")
