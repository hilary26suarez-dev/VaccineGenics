"""
Module 1: Innate Immunity and Primary Activation (TLR Pathway) — Weight: 35%

Evaluates TLR4, TLR7, TLR9 variants.
Loss-of-function variants reduce NF-κB signaling → lower innate immune activation.
"""

from dataclasses import dataclass

# Base score for a wild-type individual
BASE_SCORE = 0.70

# rsID → effect modifier for TLR pathway
TLR_EFFECTS = {
    "rs4986790": -0.35,  # TLR4 Asp299Gly — impaired LPS/PAM recognition
    "rs4986791": -0.30,  # TLR4 Thr399Ile — synergistic LOF with rs4986790 (strong LD)
    "rs179008":  -0.25,  # TLR7 Gln11Leu — X-linked, reduced ssRNA sensing
    "rs5743836": +0.20,  # TLR9 T-1237C — increased CpG-DNA promoter activity
    "rs352140":  -0.15,  # TLR9 +2848 A>G — reduced innate CpG response
    "rs2070788": +0.12,  # TMPRSS2 A>G — elevated pulmonary/mucosal expression;
                         # enhances adenoviral vector tropism and innate antigen sensing
                         # (Milewska et al. 2020; Stopsack et al. 2020 — MAF ~0.28)
}

# Zygosity multipliers: heterozygous = 0.5x, homozygous = 1.0x effect
ZYGOSITY_MULTIPLIER = {"heterozygous": 0.5, "homozygous": 1.0}


@dataclass
class TLRModuleResult:
    score: float           # 0.0 to 1.0 scale
    raw_modifier: float    # sum of all variant effects
    variants_found: list   # list of rsIDs active in this patient
    interpretation: str
    risk_flags: list


def compute_tlr_score(patient_variants: dict) -> TLRModuleResult:
    """
    Compute innate immunity score for a patient given their variant profile.

    patient_variants: dict of rsID → {copies: int, zygosity: str}
    """
    total_modifier = 0.0
    variants_found = []
    risk_flags = []

    for rsid, effect in TLR_EFFECTS.items():
        if rsid in patient_variants:
            var_info = patient_variants[rsid]
            zygosity = var_info.get("zygosity", "heterozygous")
            multiplier = ZYGOSITY_MULTIPLIER.get(zygosity, 0.5)
            contribution = effect * multiplier
            total_modifier += contribution
            variants_found.append({
                "rsid": rsid,
                "zygosity": zygosity,
                "effect": round(contribution, 3),
            })

            if effect < -0.25 and zygosity == "homozygous":
                risk_flags.append(f"RIESGO ALTO: {rsid} LOF homocigoto — señalización TLR severamente reducida")

    # Linkage Disequilibrium correction:
    # rs4986790 (TLR4 Asp299Gly) and rs4986791 (TLR4 Thr399Ile) are in near-complete LD
    # (D'≈1.0, r²≈0.9) — they virtually always co-segregate on the same haplotype.
    # Independent sampling overestimates the additive effect; apply a 50% attenuation
    # to the combined contribution when both are simultaneously detected.
    if "rs4986790" in patient_variants and "rs4986791" in patient_variants:
        contrib_4986790 = next(v["effect"] for v in variants_found if v["rsid"] == "rs4986790")
        contrib_4986791 = next(v["effect"] for v in variants_found if v["rsid"] == "rs4986791")
        combined = contrib_4986790 + contrib_4986791
        attenuated = combined * 0.5  # Haplotype carries one effective LOF event, not two
        total_modifier = total_modifier - combined + attenuated
        risk_flags.append(
            "CORRECCIÓN LD: rs4986790 + rs4986791 co-detectados — haplotipo TLR4 Asp299Gly/Thr399Ile "
            "(D'≈1.0). Efecto aditivo atenuado un 50% para evitar inflación por LD."
        )

    # Clamp score to [0.0, 1.0]
    score = max(0.0, min(1.0, BASE_SCORE + total_modifier))

    # Interpretation
    if score >= 0.75:
        interpretation = "Activación inmune innata robusta esperada. Dosis vacunal estándar adecuada."
    elif score >= 0.50:
        interpretation = "Activación innata moderada. Considerar formulación con adyuvante mejorado."
    elif score >= 0.30:
        interpretation = "Activación innata reducida. Se recomienda dosis mayor o adyuvante agonista TLR."
    else:
        interpretation = "Inmunidad innata severamente deteriorada. Probable fallo primario de vacuna — se requiere plataforma alternativa."

    return TLRModuleResult(
        score=round(score, 4),
        raw_modifier=round(total_modifier, 4),
        variants_found=variants_found,
        interpretation=interpretation,
        risk_flags=risk_flags,
    )
