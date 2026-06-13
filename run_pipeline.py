"""
VaccineGenics — Full pipeline runner.

Usage:
  python run_pipeline.py                     # Run full pipeline (offline)
  python run_pipeline.py --fetch-clinvar     # Fetch fresh ClinVar data
  python run_pipeline.py --cohort 1000       # Generate 1000 patients
  python run_pipeline.py --patient P-0001   # Analyze single patient
  python run_pipeline.py --azure             # Use Azure AI Foundry agent
"""

import argparse
import json
import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("VaccineGenics")


def run_data_pipeline(fetch_clinvar: bool = False):
    from src.data_pipeline.variant_processor import build_variant_panel
    logger.info("=== Data Pipeline ===")
    variants = build_variant_panel(use_cached=not fetch_clinvar, use_gnomad_api=True)
    logger.info(f"Variant panel: {len(variants)} curated variants")

    # Print summary by module
    from collections import Counter
    modules = Counter(v.get("module", "unknown") for v in variants)
    for module, count in modules.items():
        logger.info(f"  {module}: {count} variants")

    return variants


def run_cohort_generation(n: int = 200):
    from src.synthetic.patient_generator import generate_cohort, save_cohort
    logger.info(f"=== Generating Cohort ({n} patients) ===")
    cohort = generate_cohort(n)
    path = save_cohort(cohort)
    logger.info(f"Cohort saved: {path}")
    return cohort


def analyze_single_patient(patient_id: str, cohort=None, platform: str = "mRNA", use_azure: bool = False):
    from src.synthetic.patient_generator import load_cohort
    from src.pharmacogenomics.risk_calculator import analyze_patient
    from src.agent.foundry_agent import get_agent

    if cohort is None:
        cohort = load_cohort()

    patient = next((p for p in cohort if p.patient_id == patient_id), None)
    if patient is None:
        logger.error(f"Patient {patient_id} not found")
        return

    logger.info(f"\n=== Analyzing {patient_id} ===")
    logger.info(f"Age: {patient.age} | Sex: {patient.sex} | APOE: {patient.apoe_genotype}")

    # Deterministic engine
    report = analyze_patient(
        patient_id=patient.patient_id,
        age=patient.age,
        sex=patient.sex,
        variants=patient.variants,
        hla_haplotype=patient.hla_haplotype,
        apoe_genotype=patient.apoe_genotype,
        target_vaccine=platform,
    )

    # AI Agent chain-of-thought
    agent = get_agent(offline=not use_azure)
    patient_data = patient.to_dict()
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

    result = agent.analyze_patient(patient_data, verbose=True)
    print("\n" + "=" * 70)
    print(result["full_report"])
    print("=" * 70)

    return result


def run_cohort_analysis(cohort=None, platform: str = "mRNA", n: int = 50):
    from src.synthetic.patient_generator import get_or_generate_cohort
    from src.pharmacogenomics.risk_calculator import analyze_patient
    import json, os
    from config import PATIENTS_DIR

    if cohort is None:
        cohort = get_or_generate_cohort(n)

    logger.info(f"\n=== Cohort Analysis ({len(cohort[:n])} patients, {platform}) ===")
    reports = []
    for p in cohort[:n]:
        report = analyze_patient(
            patient_id=p.patient_id,
            age=p.age, sex=p.sex,
            variants=p.variants,
            hla_haplotype=p.hla_haplotype,
            apoe_genotype=p.apoe_genotype,
            target_vaccine=platform,
        )
        reports.append(report.to_dict())

    # Summary statistics
    from collections import Counter
    risk_counts = Counter(r["overall_risk_level"] for r in reports)
    probs = [r["irt"]["probability_protection"] for r in reports]
    seroconversions = sum(1 for r in reports if r["irt"]["seroconversion_likely"])

    logger.info(f"\n{'='*50}")
    logger.info(f"COHORT SUMMARY — {platform} Vaccine")
    logger.info(f"{'='*50}")
    logger.info(f"Patients analyzed: {len(reports)}")
    logger.info(f"Mean P(protection): {sum(probs)/len(probs):.1%}")
    logger.info(f"Seroconversion likely: {seroconversions}/{len(reports)} ({seroconversions/len(reports):.1%})")
    logger.info(f"Risk distribution:")
    for level in ["LOW", "MODERATE", "HIGH", "CRITICAL"]:
        count = risk_counts.get(level, 0)
        bar = "█" * (count * 30 // len(reports))
        logger.info(f"  {level:10s}: {count:4d} ({count/len(reports):.1%}) {bar}")

    # Save results
    os.makedirs(PATIENTS_DIR, exist_ok=True)
    out_path = os.path.join(PATIENTS_DIR, f"cohort_analysis_{platform}.json")
    with open(out_path, "w") as f:
        json.dump(reports, f, indent=2)
    logger.info(f"\nResults saved: {out_path}")
    return reports


def main():
    parser = argparse.ArgumentParser(description="VaccineGenics Pipeline Runner")
    parser.add_argument("--fetch-clinvar", action="store_true", help="Fetch fresh ClinVar data")
    parser.add_argument("--cohort", type=int, default=200, help="Cohort size to generate")
    parser.add_argument("--patient", type=str, default=None, help="Analyze single patient ID")
    parser.add_argument("--platform", default="mRNA", choices=["mRNA", "adenoviral_vector", "protein_subunit"])
    parser.add_argument("--azure", action="store_true", help="Use Azure AI Foundry agent")
    parser.add_argument("--all-platforms", action="store_true", help="Run analysis for all vaccine platforms")
    args = parser.parse_args()

    # Step 1: Data pipeline
    run_data_pipeline(fetch_clinvar=args.fetch_clinvar)

    # Step 2: Cohort generation
    cohort = run_cohort_generation(args.cohort)

    if args.patient:
        # Single patient deep dive
        analyze_single_patient(args.patient, cohort=cohort, platform=args.platform, use_azure=args.azure)
    elif args.all_platforms:
        for platform in ["mRNA", "adenoviral_vector", "protein_subunit"]:
            run_cohort_analysis(cohort=cohort, platform=platform, n=min(args.cohort, 200))
    else:
        # Standard cohort analysis
        run_cohort_analysis(cohort=cohort, platform=args.platform, n=min(args.cohort, 200))

    logger.info("\n✅ VaccineGenics pipeline complete.")


if __name__ == "__main__":
    main()
