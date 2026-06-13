"""
Cross-Platform IRT Analysis.

For a single patient genetic profile, runs the full IRT pipeline
across all 3 vaccine platforms simultaneously and returns a comparative
DataFrame + recommendation matrix.

This is what makes VaccineGenics truly powerful:
  "Same DNA, different vaccine — which one fits YOU?"
"""

from dataclasses import dataclass
from typing import Optional
import math
import numpy as np

from .irt_model import irt_4pl, compute_theta, IRTResult, compute_confidence_interval, apply_demographic_adjustments
from .modules.immunocompromised_module import (
    ImmunocompromisedResult,
    SpecialCondition,
    THETA_PENALTY,
    PLATFORM_B_ADJUSTMENT,
    DOSE_MULTIPLIER,
)

from config import VACCINE_IRT_PARAMS


PLATFORM_LABELS = {
    "mRNA":              "ARNm (BNT162b2 / mRNA-1273)",
    "adenoviral_vector": "Vector Adenoviral (ChAdOx1 / Ad26)",
    "protein_subunit":   "Subunidad Proteica (NVX-CoV2373 / RBD-dimer)",
}


@dataclass
class PlatformComparison:
    platform: str
    label: str
    theta_adjusted: float
    probability_protection: float
    confidence_interval: tuple
    seroconversion_likely: bool
    b_final: float
    dose_multiplier: float
    safety_concerns: list
    recommendation_rank: int     # 1 = best for this patient, 3 = worst


@dataclass
class CrossPlatformReport:
    patient_id: str
    theta_base: float            # from genetic modules only
    theta_adjusted: float        # after immunocompromised penalty
    special_condition: SpecialCondition
    platforms: list              # list of PlatformComparison
    best_platform: str
    contraindicated_platforms: list
    overall_summary: str


def _apply_immunocompromised_adjustments(
    theta: float,
    platform: str,
    condition: SpecialCondition,
    age: int,
    sex: str,
) -> tuple[float, float, float, float]:
    """
    Apply condition-specific θ penalty and b/c adjustments.
    Returns (theta_adjusted, b_final, c_final, dose_multiplier).
    """
    penalty = THETA_PENALTY.get(condition, 0.0)
    theta_adj = theta + penalty

    params = VACCINE_IRT_PARAMS[platform]
    b_base = params["b"]
    b_adj = PLATFORM_B_ADJUSTMENT.get(condition, {}).get(platform, 0.0)
    b_final = b_base + b_adj
    c = params["c"]

    # Shared demographic adjustments — same function as irt_model.run_irt_analysis
    b_final, c = apply_demographic_adjustments(b_final, c, age, sex)

    dose_mult = DOSE_MULTIPLIER.get(condition, 1.0)
    return theta_adj, b_final, c, dose_mult


def run_cross_platform_irt(
    patient_id: str,
    score_tlr: float,
    score_hla: float,
    score_stat: float,
    score_apoe: float,
    special_condition: SpecialCondition = SpecialCondition.NONE,
    age: int = 30,
    sex: str = "Unknown",
    immunocompromised_result: Optional[ImmunocompromisedResult] = None,
    contraindicated_platforms: list = None,
) -> CrossPlatformReport:
    """
    Run IRT analysis for all platforms and rank them for this patient's DNA.
    Returns a CrossPlatformReport with comparative metrics.
    """
    theta_base = compute_theta(score_tlr, score_hla, score_stat, score_apoe)
    contraindicated = contraindicated_platforms or []

    platform_results = []
    for platform in ["mRNA", "adenoviral_vector", "protein_subunit"]:
        params = VACCINE_IRT_PARAMS[platform]
        a = params["a"]

        theta_adj, b_final, c_adj, dose_mult = _apply_immunocompromised_adjustments(
            theta_base, platform, special_condition, age, sex
        )

        prob = irt_4pl(theta_adj, a, b_final, c_adj)
        ci = compute_confidence_interval(theta_adj, platform)
        seroconv = prob >= 0.60

        # Collect safety concerns
        safety = []
        if immunocompromised_result:
            plat_flag = immunocompromised_result.safety_flags.get(platform)
            if plat_flag:
                safety.append(plat_flag)
        if platform in contraindicated:
            safety.append(f"CONTRAINDICADO: {platform} — contraindicación genética/clínica detectada")

        platform_results.append(PlatformComparison(
            platform=platform,
            label=PLATFORM_LABELS[platform],
            theta_adjusted=round(theta_adj, 4),
            probability_protection=round(prob, 4),
            confidence_interval=ci,
            seroconversion_likely=seroconv,
            b_final=round(b_final, 4),
            dose_multiplier=dose_mult,
            safety_concerns=safety,
            recommendation_rank=0,  # set below
        ))

    # Rank: exclude contraindicated, then sort by probability descending
    valid = [p for p in platform_results if p.platform not in contraindicated]
    invalid = [p for p in platform_results if p.platform in contraindicated]

    valid.sort(key=lambda p: p.probability_protection, reverse=True)
    for i, p in enumerate(valid, start=1):
        p.recommendation_rank = i
    for p in invalid:
        p.recommendation_rank = len(valid) + 1  # rank last

    all_platforms = valid + invalid

    best = valid[0].platform if valid else "protein_subunit"
    theta_adj_best = theta_base + THETA_PENALTY.get(special_condition, 0.0)

    # Build summary
    best_prob = valid[0].probability_protection if valid else 0.0
    summary_lines = [
        f"Paciente {patient_id} | θ_base={theta_base:+.3f} | Condición: {special_condition.value}",
        f"θ_ajustado={theta_adj_best:+.3f} (penalización={THETA_PENALTY.get(special_condition,0.0):+.2f})",
        "",
    ]
    for p in all_platforms:
        rank_str = f"#{p.recommendation_rank}" if p.platform not in contraindicated else "❌ CONTRAINDICADO"
        sero_str = "✓ SEROCONVERSIÓN PROBABLE" if p.seroconversion_likely else "✗ RIESGO DE FALLO"
        summary_lines.append(
            f"  [{rank_str}] {p.label}\n"
            f"       P(protección)={p.probability_protection:.1%}  "
            f"IC=[{p.ci_lower_str()}–{p.ci_upper_str()}]  "
            f"{sero_str}  "
            f"Dosis: {p.dose_multiplier}×"
        )

    summary_lines.append(f"\n→ PLATAFORMA RECOMENDADA: {PLATFORM_LABELS[best]}")
    if best_prob < 0.40:
        summary_lines.append(
            "ADVERTENCIA: La mejor plataforma disponible aún tiene una probabilidad de protección < 40%. "
            "La profilaxis pasiva (anticuerpos monoclonales) podría ser la estrategia primaria."
        )

    return CrossPlatformReport(
        patient_id=patient_id,
        theta_base=round(theta_base, 4),
        theta_adjusted=round(theta_adj_best, 4),
        special_condition=special_condition,
        platforms=all_platforms,
        best_platform=best,
        contraindicated_platforms=contraindicated,
        overall_summary="\n".join(summary_lines),
    )


# Monkey-patch ci helper onto PlatformComparison after the fact
def _ci_lower_str(self):
    return f"{self.confidence_interval[0]:.1%}"
def _ci_upper_str(self):
    return f"{self.confidence_interval[1]:.1%}"
PlatformComparison.ci_lower_str = _ci_lower_str
PlatformComparison.ci_upper_str = _ci_upper_str


def cross_platform_dataframe(report: CrossPlatformReport) -> list[dict]:
    """Return a list of dicts suitable for pd.DataFrame construction."""
    rows = []
    for p in report.platforms:
        rows.append({
            "Plataforma": p.label,
            "θ_ajustado": p.theta_adjusted,
            "P(Protección)": p.probability_protection,
            "IC_inferior": p.confidence_interval[0],
            "IC_superior": p.confidence_interval[1],
            "Seroconversión": p.seroconversion_likely,
            "Multiplicador Dosis": p.dose_multiplier,
            "Posición": p.recommendation_rank,
            "Contraindicada": p.platform in report.contraindicated_platforms,
            "Alertas de Seguridad": "; ".join(p.safety_concerns) if p.safety_concerns else "",
        })
    return rows
