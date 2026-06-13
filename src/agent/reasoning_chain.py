"""
Chain-of-Thought reasoning chain builder.

Constructs the explicit multi-step reasoning prompt that the Azure AI Foundry
agent uses when analyzing a patient. This makes the reasoning process fully
transparent and traceable — critical for the hackathon judging criteria.
"""

import json
from datetime import datetime


def build_patient_analysis_prompt(patient_data: dict) -> str:
    """
    Build a detailed analysis prompt for the agent that forces
    explicit 5-step chain-of-thought reasoning.
    """
    pid = patient_data.get("patient_id", "UNKNOWN")
    age = patient_data.get("age", 0)
    sex = patient_data.get("sex", "Unknown")
    apoe = patient_data.get("apoe_genotype", "ε3/ε3")
    variants = patient_data.get("variants", {})
    hla = patient_data.get("hla_haplotype", {})
    platform = patient_data.get("target_vaccine", "mRNA")

    # Serialize key data for the agent
    variant_list = list(variants.keys())
    hla_alleles_flat = []
    for cls in hla.values():
        for locus, alleles in cls.items():
            if isinstance(alleles, list):
                hla_alleles_flat.extend(alleles)

    prompt = f"""
Analyze the following synthetic patient profile using the VaccineGenics 5-step chain-of-thought protocol.

## Patient Profile
- Patient ID: {pid}
- Age: {age} years
- Sex: {sex}
- APOE Genotype: {apoe}
- Target Vaccine Platform: {platform}

## Genetic Variants Present
{json.dumps(variant_list, indent=2)}

## Variant Details (zygosity)
{json.dumps(variants, indent=2)}

## HLA Haplotype
Class I alleles: {[a for a in hla_alleles_flat if 'HLA-A' in a or 'HLA-B' in a or 'HLA-C' in a]}
Class II alleles: {[a for a in hla_alleles_flat if 'DRB1' in a or 'DQB1' in a]}

## Pre-computed Module Scores (from deterministic engine)
{json.dumps(patient_data.get("module_scores", {}), indent=2)}

## Pre-computed IRT Result
{json.dumps(patient_data.get("irt", {}), indent=2)}

---

INSTRUCTIONS:
Follow the exact 5-step VaccineGenics reasoning protocol.

For STEP 4, use the Code Interpreter tool to execute the IRT 4PL calculation with Python/numpy to confirm
the pre-computed probability and show the mathematical work explicitly.

For STEP 2, search the knowledge base (File Search) for relevant literature on any critical variants
you identify (especially if HLA-DRB1*11:04, APOE ε4, TLR4 LOF variants, or IL-6 rs1800795 are present).

Show ALL intermediate calculations. Do not skip steps. Your reasoning chain will be evaluated.
""".strip()
    return prompt


def format_chain_of_thought_steps(steps: list[dict]) -> str:
    """Format the agent's reasoning steps as a human-readable trace."""
    lines = ["=== VaccineGenics Chain-of-Thought Trace ===", ""]
    for i, step in enumerate(steps, 1):
        lines.append(f"[STEP {i}] {step.get('name', f'Step {i}')}")
        lines.append(f"  Tool: {step.get('tool', 'LLM reasoning')}")
        lines.append(f"  Input: {str(step.get('input', ''))[:200]}")
        lines.append(f"  Output: {str(step.get('output', ''))[:400]}")
        lines.append("")
    return "\n".join(lines)


def extract_recommendation_from_response(agent_response: str) -> dict:
    """Parse the structured recommendation from agent output."""
    result = {
        "platform": None,
        "dose_recommendation": None,
        "protection_probability": None,
        "risk_flags": [],
        "full_report": agent_response,
    }

    # Scan for the LAST complete JSON object in the response (the JSON SUMMARY block).
    # Using rfind("{") then walking backward avoids the "first { to last }" greedy bug
    # when the agent outputs multiple JSON objects (e.g. code snippets + final summary).
    import re as _re
    for m in reversed(list(_re.finditer(r'\{', agent_response))):
        start = m.start()
        # Find the matching closing brace using a bracket counter
        depth, end = 0, -1
        for i, ch in enumerate(agent_response[start:], start=start):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i
                    break
        if end == -1:
            continue
        candidate = agent_response[start:end + 1]
        try:
            structured = json.loads(candidate)
            # Only accept objects that look like VaccineGenics reports
            if any(k in structured for k in ("platform", "vaccine_platform",
                                              "protection_probability", "dose_recommendation")):
                result["platform"] = structured.get("platform") or structured.get("vaccine_platform")
                result["dose_recommendation"] = structured.get("dose_recommendation")
                result["protection_probability"] = structured.get("protection_probability")
                if isinstance(structured.get("risk_flags"), list):
                    result["risk_flags"] = structured.get("risk_flags")
                return result
        except json.JSONDecodeError:
            continue

    lines = agent_response.split("\n")
    for line in lines:
        if "P(Protection)" in line or "protection probability" in line.lower():
            import re
            match = re.search(r"(\d+\.?\d*)\s*%", line)
            if match:
                result["protection_probability"] = float(match.group(1)) / 100

        if "PLATFORM:" in line.upper():
            result["platform"] = line.split(":", 1)[-1].strip()

        if "DOSE" in line.upper() and result["dose_recommendation"] is None:
            result["dose_recommendation"] = line.strip()

        if any(kw in line for kw in ["CONTRAINDICATION", "MYOCARDITIS RISK", "LNP DELIVERY RISK"]):
            result["risk_flags"].append(line.strip())

    return result
