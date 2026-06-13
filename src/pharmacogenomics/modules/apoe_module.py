"""
Module 4: LNP Biodisponibility and Lipid Clearance (APOE/PEG3 Pathway) — Weight: 5%

Governs how efficiently mRNA-LNP vaccines are delivered, internalized, and cleared.
APOE ε4 prolongs LNP tissue retention → mitochondrial stress, local inflammation.
PEG3 variants alter lipid metabolism → potential PEG excipient sensitivity.
"""

from dataclasses import dataclass

BASE_SCORE = 0.75

# NOTE: rs429358 and rs7412 define the APOE isoform and are already encoded in
# APOE_GENOTYPE_EFFECTS via the apoe_genotype string. They are intentionally EXCLUDED
# here to prevent double-counting the same biological effect.
# Only non-genotype-defining APOE-pathway SNPs belong in this dict (e.g., PEG3 variants).
APOE_EFFECTS: dict = {}  # Reserved for future PEG3 / lipid-pathway SNPs not encoded in genotype

APOE_GENOTYPE_EFFECTS = {
    "ε4/ε4": -0.50,
    "ε3/ε4": -0.35,
    "ε2/ε4": -0.20,
    "ε3/ε3":  0.00,
    "ε2/ε3": +0.10,
    "ε2/ε2": +0.15,
}

ZYGOSITY_MULTIPLIER = {"heterozygous": 0.5, "homozygous": 1.0}


@dataclass
class APOEModuleResult:
    score: float
    raw_modifier: float
    apoe_genotype: str
    peg_sensitivity_risk: bool
    lnp_clearance_profile: str    # "normal", "reduced", "impaired"
    platform_recommendation: str  # Which vaccine platform is safest
    interpretation: str
    risk_flags: list


def compute_apoe_score(
    patient_variants: dict,
    apoe_genotype: str = "ε3/ε3",
) -> APOEModuleResult:
    """
    Compute LNP biodisponibility score.

    patient_variants: rsID → {copies, zygosity}
    apoe_genotype: pre-derived APOE isoform string (e.g. "ε3/ε4")
    """
    risk_flags = []

    # Use genotype-level modifier if available
    genotype_modifier = APOE_GENOTYPE_EFFECTS.get(apoe_genotype, 0.0)

    # Also check individual variant contributions (PEG3 and other APOE-linked)
    variant_modifier = 0.0
    for rsid, effect in APOE_EFFECTS.items():
        if rsid in patient_variants:
            var_info = patient_variants[rsid]
            zygosity = var_info.get("zygosity", "heterozygous")
            multiplier = ZYGOSITY_MULTIPLIER.get(zygosity, 0.5)
            variant_modifier += effect * multiplier * 0.3  # Partial weight since genotype handles main effect

    total_modifier = genotype_modifier + variant_modifier
    score = max(0.0, min(1.0, BASE_SCORE + total_modifier))

    # PEG sensitivity risk: APOE ε4 increases local inflammatory response to PEGylated excipients
    peg_sensitivity = apoe_genotype in ("ε4/ε4", "ε3/ε4")

    # LNP clearance profile
    if score >= 0.70:
        lnp_clearance = "normal"
    elif score >= 0.50:
        lnp_clearance = "reduced"
    else:
        lnp_clearance = "impaired"

    # Platform recommendation based on lipid metabolism profile
    if score < 0.45:
        platform_recommendation = (
            "protein_subunit — Evitar plataforma ARNm-LNP por aclaramiento lipídico deteriorado "
            "y riesgo de estrés mitocondrial mediado por APOE ε4."
        )
        risk_flags.append(
            f"RIESGO DE ENTREGA LNP: APOE {apoe_genotype} — retención prolongada de LNP en tejido. "
            "Se recomienda cambiar de ARNm-LNP a plataforma de subunidad proteica."
        )
    elif score < 0.60:
        platform_recommendation = (
            "mRNA — Proceder con ARNm-LNP pero reducir concentración de excipiente lipídico. "
            "Monitorizar reacción en el sitio de inyección durante 48h."
        )
        risk_flags.append(f"RIESGO MODERADO DE LNP: APOE {apoe_genotype} — aclaramiento reducido, monitorizar sitio de inyección.")
    else:
        platform_recommendation = "mRNA — Formulación LNP estándar apropiada. Sin preocupaciones de metabolismo lipídico."

    if peg_sensitivity:
        risk_flags.append(
            f"ALERTA PEG: APOE {apoe_genotype} — mayor riesgo de reacción a excipiente PEGilado. "
            "Cribado de IgE anti-PEG si hay antecedentes de anafilaxia inexplicada."
        )

    # Interpretation
    if score >= 0.70:
        interpretation = "Biodistribución y aclaramiento de LNP normal. La entrega de vacuna ARNm será eficiente."
    elif score >= 0.50:
        interpretation = f"Aclaramiento de LNP reducido (APOE {apoe_genotype}). Una estrategia de espaciado de dosis puede mitigar el riesgo."
    else:
        interpretation = (
            f"Metabolismo lipídico deteriorado (APOE {apoe_genotype}). La plataforma ARNm-LNP conlleva riesgo elevado "
            "de estrés mitocondrial. Se prefiere fuertemente la plataforma de subunidad proteica."
        )

    return APOEModuleResult(
        score=round(score, 4),
        raw_modifier=round(total_modifier, 4),
        apoe_genotype=apoe_genotype,
        peg_sensitivity_risk=peg_sensitivity,
        lnp_clearance_profile=lnp_clearance,
        platform_recommendation=platform_recommendation,
        interpretation=interpretation,
        risk_flags=risk_flags,
    )
