"""
Module 2: Antigen Presentation and Cellular Memory (HLA Pathway) — Weight: 40%

Highest-weighted module: HLA determines adaptive immune response quality,
NAb titers, and autoimmune risk (adversomics).
"""

from dataclasses import dataclass

BASE_SCORE = 0.65

# HLA efficacy alleles: positive effect on NAb titers and CD4+ response
HLA_EFFICACY = {
    "HLA-A*02:01":    +0.40,
    "HLA-B*40:01":    +0.30,
    "HLA-DRB1*03:01": +0.35,
    "HLA-DQB1*06:02": +0.25,
    "HLA-B*57:01":    +0.20,
    "HLA-A*01:01":    +0.10,
    "HLA-DRB1*15:01": +0.15,
}

# HLA risk alleles: associated with vaccine-induced autoimmunity or suboptimal response
HLA_RISK = {
    "HLA-DRB1*11:04": -0.50,  # VITT risk with adenoviral vectors
    "HLA-B*35:01":    -0.30,  # Suboptimal response
    "HLA-C*07:01":    -0.25,  # Reduced protection
    "HLA-DRB1*01:01": -0.20,  # Lower NAb titers
    "HLA-B*35:03":    -0.35,  # Post-vaccine thyroiditis risk
    "HLA-C*04:01":    -0.30,  # Autoimmune thyroiditis
    "HLA-DRB1*07:01": -0.10,  # Mild reduction
}

# Vaccine-specific HLA risk matrix
PLATFORM_SPECIFIC_RISK = {
    "adenoviral_vector": {
        "HLA-DRB1*11:04": "VITT (trombocitopenia e trombosis inducidas por vacuna) — CONTRAINDICADO",
    },
    "mRNA": {
        "HLA-B*35:01": "Riesgo elevado de miocarditis en varones adolescentes",
        "HLA-C*07:01": "Riesgo elevado de miocarditis",
    },
}


@dataclass
class HLAModuleResult:
    score: float
    raw_modifier: float
    efficacy_alleles: list
    risk_alleles: list
    autoimmune_risk_score: float   # 0.0 = no risk, 1.0 = extreme risk
    platform_contraindications: dict
    interpretation: str
    risk_flags: list


def _flatten_hla_alleles(hla_haplotype: dict) -> list[str]:
    """Extract all HLA alleles from the nested haplotype structure."""
    alleles = []
    for cls_key, cls_val in hla_haplotype.items():
        for locus, locus_alleles in cls_val.items():
            if isinstance(locus_alleles, list):
                alleles.extend(locus_alleles)
            else:
                alleles.append(locus_alleles)
    return alleles


def compute_hla_score(hla_haplotype: dict, target_platform: str = "mRNA") -> HLAModuleResult:
    """
    Compute HLA presentation score and autoimmune risk.

    hla_haplotype: {class_I: {HLA-A: [...], HLA-B: [...]}, class_II: {...}}
    """
    alleles = _flatten_hla_alleles(hla_haplotype)
    total_modifier = 0.0
    efficacy_alleles = []
    risk_alleles = []
    risk_flags = []
    autoimmune_score = 0.0
    platform_contraindications = {}

    for allele in alleles:
        # Efficacy check
        if allele in HLA_EFFICACY:
            effect = HLA_EFFICACY[allele]
            total_modifier += effect * 0.5  # Each allele contributes (diploid)
            efficacy_alleles.append({"allele": allele, "effect": round(effect, 3)})

        # Risk check
        if allele in HLA_RISK:
            effect = HLA_RISK[allele]
            total_modifier += effect * 0.5
            risk_alleles.append({"allele": allele, "effect": round(effect, 3)})
            autoimmune_score += abs(effect) * 0.3

            if abs(effect) >= 0.35:
                risk_flags.append(f"RIESGO AUTOINMUNE: {allele} — modificador adverso del {abs(effect):.0%}")

        # Platform-specific contraindications
        for platform, risk_map in PLATFORM_SPECIFIC_RISK.items():
            if allele in risk_map:
                platform_contraindications.setdefault(platform, []).append(
                    f"{allele}: {risk_map[allele]}"
                )
                if platform == target_platform:
                    risk_flags.append(f"RIESGO DE PLATAFORMA [{platform.upper()}]: {allele} — {risk_map[allele]}")

    score = max(0.0, min(1.0, BASE_SCORE + total_modifier))
    autoimmune_score = min(1.0, autoimmune_score)

    # Interpretation
    if score >= 0.80:
        interpretation = "Excelente capacidad de presentación de antígenos. Se espera respuesta fuerte de NAb y células T de memoria."
    elif score >= 0.60:
        interpretation = "Presentación mediada por HLA adecuada. Se recomienda protocolo de dosificación estándar."
    elif score >= 0.40:
        interpretation = "Unión HLA-péptido subóptima predicha. Considerar programación de dosis de refuerzo."
    else:
        interpretation = "Perfil de presentación de antígenos deficiente. Probable fallo de seroconversión — monitorización clínica requerida."

    if autoimmune_score > 0.5:
        interpretation += " ADVERTENCIA: Riesgo elevado de eventos adversos autoinmunes detectado."

    return HLAModuleResult(
        score=round(score, 4),
        raw_modifier=round(total_modifier, 4),
        efficacy_alleles=efficacy_alleles,
        risk_alleles=risk_alleles,
        autoimmune_risk_score=round(autoimmune_score, 4),
        platform_contraindications=platform_contraindications,
        interpretation=interpretation,
        risk_flags=risk_flags,
    )
