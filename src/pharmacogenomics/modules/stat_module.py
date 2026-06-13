"""
Module 3: Inflammatory Amplification / STAT-Cytokine Pathway — Weight: 20%

IL-6 polymorphisms and STAT1/STAT3 variants modulate post-vaccine
inflammatory amplification. Double-edged sword:
  - High IL-6 responders → higher IgG titers (benefit)
  - High IL-6 responders → elevated myocarditis risk via STAT3 (risk)
"""

from dataclasses import dataclass

BASE_SCORE = 0.60

STAT_EFFECTS = {
    # IL-6 promoter variants
    "rs1800795": +0.30,  # GG homozygous = high IL-6 → superior IgG
    "rs1800796": +0.15,  # IL-6 promoter moderate
    "rs1800797": +0.20,  # IL-6 promoter

    # STAT pathway
    "rs1137578":  -0.20,  # STAT3 LOF
    "rs12233781": +0.15,  # STAT1 gain-of-function
}

# Variants that increase myocarditis / cytokine storm risk
INFLAMMATORY_RISK_VARIANTS = {"rs1800795", "rs1800796", "rs1800797"}
MYOCARDITIS_RISK_THRESHOLD = 0.55  # Score above this in inflammatory module → flag myocarditis

ZYGOSITY_MULTIPLIER = {"heterozygous": 0.5, "homozygous": 1.0}


@dataclass
class STATModuleResult:
    score: float
    raw_modifier: float
    variants_found: list
    il6_hyperexpression_risk: bool
    myocarditis_risk_elevated: bool
    cytokine_storm_risk: float      # 0.0 to 1.0
    interpretation: str
    risk_flags: list


def compute_stat_score(patient_variants: dict, patient_sex: str = "Unknown", patient_age: int = 30) -> STATModuleResult:
    """
    Compute cytokine/STAT inflammatory amplification score.
    Sex and age are used for myocarditis risk stratification
    (adolescent males are highest-risk group for post-mRNA myocarditis).
    """
    total_modifier = 0.0
    variants_found = []
    risk_flags = []
    il6_pro_count = 0
    cytokine_storm_risk = 0.0

    for rsid, effect in STAT_EFFECTS.items():
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

            if rsid in INFLAMMATORY_RISK_VARIANTS and zygosity == "homozygous":
                il6_pro_count += 1
                cytokine_storm_risk += 0.15

    score = max(0.0, min(1.0, BASE_SCORE + total_modifier))
    il6_hyperexpression = il6_pro_count >= 2
    cytokine_storm_risk = min(1.0, cytokine_storm_risk)

    # Count ANY IL-6 pro-expression variants (het or hom) for compound risk
    total_il6_variants = sum(
        1 for rsid in INFLAMMATORY_RISK_VARIANTS if rsid in patient_variants
    )
    # Weighted IL-6 burden: hom=1.0, het=0.5 per variant
    il6_burden = sum(
        (1.0 if patient_variants[rsid].get("zygosity") == "homozygous" else 0.5)
        for rsid in INFLAMMATORY_RISK_VARIANTS if rsid in patient_variants
    )

    # Myocarditis risk: elevated IL-6 burden + young male
    # Triggers on: (a) any hom IL-6 variant in young male, OR
    #              (b) multiple het IL-6 variants (burden >= 1.5) in young male, OR
    #              (c) >= 2 hom IL-6 variants regardless of sex
    myocarditis_elevated = False
    young_male = patient_sex == "Male" and patient_age <= 30
    if score > MYOCARDITIS_RISK_THRESHOLD:
        if young_male and (il6_pro_count >= 1 or il6_burden >= 1.5):
            myocarditis_elevated = True
            risk_flags.append(
                "RIESGO DE MIOCARDITIS: hiperexpresión de IL-6 + perfil de varón joven. "
                "Monitorización post-vacuna ARNm requerida (ECG + troponina a las 72h)."
            )
        elif il6_pro_count >= 2:
            myocarditis_elevated = True
            risk_flags.append("RIESGO ELEVADO DE CITOCINAS: Múltiples variantes de pro-expresión de IL-6 detectadas.")

    if il6_hyperexpression:
        risk_flags.append("HIPEREXPRESIÓN DE IL-6: GG homocigoto rs1800795 — IgG elevada pero con riesgo inflamatorio.")

    # Interpretation
    if score >= 0.75:
        interpretation = (
            "Alta amplificación de citocinas. Se esperan títulos de anticuerpos superiores. "
            "Monitorizar reactogenicidad sistémica."
        )
    elif score >= 0.50:
        interpretation = "Amplificación inflamatoria moderada. Se predice respuesta inmune estándar."
    else:
        interpretation = "Baja amplificación de citocinas. Puede requerir dosis de refuerzo adicionales para títulos adecuados."

    return STATModuleResult(
        score=round(score, 4),
        raw_modifier=round(total_modifier, 4),
        variants_found=variants_found,
        il6_hyperexpression_risk=il6_hyperexpression,
        myocarditis_risk_elevated=myocarditis_elevated,
        cytokine_storm_risk=round(cytokine_storm_risk, 4),
        interpretation=interpretation,
        risk_flags=risk_flags,
    )
