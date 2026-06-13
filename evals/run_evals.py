"""
VaccineGenics Evaluation Runner.

Usage:
  python evals/run_evals.py
  python evals/run_evals.py --verbose

Runs 8 synthetic eval cases through the pharmacogenomics engine and reports
accuracy against expected platform recommendations.

Target: accuracy >= 80%.
"""

from __future__ import annotations

import json
import os
import sys
import argparse
import textwrap

# ── Path setup — allow running from repo root or evals/ dir ──────────────────
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_SRC_DIR = os.path.join(_REPO_ROOT, "src")
for _path in (_SRC_DIR, _REPO_ROOT):
    if _path not in sys.path:
        sys.path.insert(0, _path)

# Force UTF-8 output on Windows console (handles unicode chars in output)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except AttributeError:
        pass

from pharmacogenomics.risk_calculator import analyze_patient
from pharmacogenomics.modules.immunocompromised_module import SpecialCondition


def _build_hla_dict(hla_str: str) -> dict:
    """Convert 'HLA-A*02:01,HLA-DRB1*07:01' to the nested dict format the engine expects."""
    alleles = [h.strip() for h in hla_str.split(",") if h.strip()]
    class_i: dict = {}
    class_ii: dict = {}
    for allele in alleles:
        base = allele.split("*")[0]   # e.g. "HLA-DRB1"
        gene = base.replace("HLA-", "")   # e.g. "DRB1"
        if gene in ("A", "B", "C"):
            class_i.setdefault(base, []).append(allele)
        else:
            class_ii.setdefault(base, []).append(allele)
    if not class_i:
        class_i = {"HLA-A": ["HLA-A*02:01"]}
    if not class_ii:
        class_ii = {"HLA-DRB1": ["HLA-DRB1*07:01"]}
    return {"class_I": class_i, "class_II": class_ii}

_CASES_PATH = os.path.join(os.path.dirname(__file__), "eval_cases.json")

# Platform name normalisation — engine slug → eval expected string
_PLAT_MAP = {
    "mRNA": "mRNA-LNP",
    "adenoviral_vector": "Adenoviral",
    "protein_subunit": "Subunidad Proteica",
}


def _load_cases() -> list:
    with open(_CASES_PATH, encoding="utf-8") as f:
        return json.load(f)["cases"]


def _run_case(case: dict) -> dict:
    """Run one eval case; return the case dict augmented with results."""
    profile = case["profile"]
    condition_slug = profile.get("special_condition", "none")

    try:
        condition = SpecialCondition(condition_slug)
    except ValueError:
        condition = SpecialCondition.NONE

    # Build variants from profile flags
    variants: dict = {}
    tlr4_flag = profile.get("tlr4_variant", "rs4986790_wt")
    if tlr4_flag == "rs4986790_risk":
        variants["rs4986790"] = {"genotype": "A/G", "risk_allele": "A", "gene": "TLR4"}
        variants["rs4986791"] = {"genotype": "T/C", "risk_allele": "T", "gene": "TLR4"}

    hla_str = profile.get("hla_haplotype", "HLA-A*02:01,HLA-DRB1*07:01")
    hla_dict = _build_hla_dict(hla_str)
    target_vaccine = profile.get("target_vaccine", "mRNA")

    report = analyze_patient(
        patient_id=case["case_id"],
        age=profile.get("age", 35),
        sex=profile.get("sex", "Male"),
        variants=variants,
        hla_haplotype=hla_dict,
        apoe_genotype=profile.get("apoe_genotype", "ε3/ε3"),
        target_vaccine=target_vaccine,
        special_condition=condition,
        run_cross_platform=True,
    )
    rd = report.to_dict()

    # Best non-contraindicated platform from cross-platform analysis
    cp = rd.get("cross_platform", [])
    best = sorted(
        [r for r in cp if not r.get("contraindicated", False)],
        key=lambda x: x.get("rank", 99)
    )
    actual_slug = best[0].get("platform", "mRNA") if best else "mRNA"
    actual_p = best[0].get("probability_protection", 0.0) if best else 0.0
    actual_label = _PLAT_MAP.get(actual_slug, actual_slug)

    expected_label = case.get("expected_platform", "")
    is_match = actual_label == expected_label

    return {
        **case,
        "actual_platform": actual_label,
        "actual_p_protection": actual_p,
        "is_match": is_match,
        "overall_risk": rd.get("overall_risk_level", "?"),
        "theta": rd.get("irt", {}).get("theta", 0.0),
    }


def run_eval_set(verbose: bool = False) -> dict:
    """Run all eval cases and return aggregated results dict."""
    cases = _load_cases()
    results = []
    errors = []

    for case in cases:
        try:
            result = _run_case(case)
            results.append(result)
        except Exception as exc:
            errors.append({"case_id": case.get("case_id", "?"), "error": str(exc)})
            results.append({
                **case,
                "actual_platform": "ERROR",
                "actual_p_protection": 0.0,
                "is_match": False,
                "error": str(exc),
            })

    correct = sum(1 for r in results if r.get("is_match", False))
    total = len(results)
    accuracy = correct / total if total else 0.0

    return {
        "cases": results,
        "correct": correct,
        "total": total,
        "accuracy": accuracy,
        "errors": errors,
        "passed": accuracy >= 0.80,
    }


def _print_results(results: dict, verbose: bool) -> None:
    """Pretty-print eval results to stdout."""
    accuracy = results["accuracy"]
    status = "[PASSED]" if results["passed"] else "[FAILED]"
    print()
    print("=" * 65)
    print(f"  VaccineGenics Eval Set  —  {results['correct']}/{results['total']} correct")
    print(f"  Accuracy: {accuracy:.1%}   {status}  (target ≥ 80%)")
    print("=" * 65)
    print()

    header = f"  {'Case':<12} {'Expected':<22} {'Actual':<22} {'P(act)':<8} {'OK'}"
    print(header)
    print("  " + "-" * 63)

    for r in results["cases"]:
        ok = " OK" if r.get("is_match") else " --"
        exp = r.get("expected_platform", "?")[:20]
        act = r.get("actual_platform", "?")[:20]
        p = r.get("actual_p_protection", 0.0)
        case_id = r.get("case_id", "?")
        print(f"  {case_id:<12} {exp:<22} {act:<22} {p:<8.1%} {ok}")
        if verbose:
            explanation = r.get("explanation", "")
            if explanation:
                for line in textwrap.wrap(explanation, width=58):
                    print(f"    {line}")
            if r.get("error"):
                print(f"    ⚠️  ERROR: {r['error']}")
            theta = r.get("theta", 0.0)
            risk = r.get("overall_risk", "?")
            print(f"    θ = {theta:+.4f}  ·  Risk: {risk}")
            print()

    if results["errors"]:
        print()
        print(f"  ⚠️  {len(results['errors'])} case(s) threw exceptions:")
        for e in results["errors"]:
            print(f"     {e['case_id']}: {e['error']}")

    print()
    if results["passed"]:
        print("  ✅ Eval set meets accuracy target (≥ 80%). Demo-ready.")
    else:
        print("  ❌ Accuracy below 80% target. Review eval_cases.json mappings.")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VaccineGenics eval runner")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show per-case explanations and theta values")
    parser.add_argument("--json", action="store_true",
                        help="Output results as JSON")
    args = parser.parse_args()

    output = run_eval_set(verbose=args.verbose)

    if args.json:
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        _print_results(output, verbose=args.verbose)

    sys.exit(0 if output["passed"] else 1)
