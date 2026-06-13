"""
IRT 4PL (Four-Parameter Logistic) Model adapted for pharmacogenomics.

Maps the psychometric Item Response Theory framework to immunological response:

  P(Protective Response | θ) = c + (1 - c) × [1 / (1 + exp(-a × (θ - b)))]

Parameters:
  θ (theta) — Net Immunogenic Capacity of patient (from module scores)
  b — Activation Threshold / Vaccine Difficulty
  a — Biomarker Discrimination / Curve Steepness
  c — Baseline Immunological Response / Lower Asymptote (never truly 0)
"""

import math
import numpy as np
from dataclasses import dataclass
from typing import Optional

from config import MODULE_WEIGHTS, VACCINE_IRT_PARAMS


@dataclass
class IRTResult:
    theta: float                    # θ_clinical = θ_genetic + condition_penalty
    theta_genetic: float            # θ from genetic modules only (no condition penalty)
    theta_penalty: float            # Additive penalty from immunocompromised condition
    probability_protection: float   # P(protective response) from 4PL
    vaccine_platform: str
    a: float                        # Discrimination parameter
    b: float                        # Final difficulty (base + b_extra + demographics)
    b_base: float                   # Platform base b (before any adjustments)
    c: float                        # Lower asymptote (baseline immunity)
    dose_recommendation: str
    confidence_interval: tuple      # (lower_95, upper_95)
    seroconversion_likely: bool
    interpretation: str


def compute_theta(
    score_tlr: float,
    score_hla: float,
    score_stat: float,
    score_apoe: float,
) -> float:
    """
    Compute θ: weighted sum of module scores, centered around 0.

    θ = (0.35 × Score_TLR) + (0.40 × Score_HLA) + (0.20 × Score_STAT) + (0.05 × Score_APOE)

    Scores are in [0.0, 1.0]. We center θ around 0 by subtracting 0.65 (expected baseline).
    This maps:
      - Strong responder (all scores ~0.85): θ ≈ +0.20
      - Average responder (all scores ~0.65): θ ≈ 0.0
      - Poor responder (all scores ~0.30):   θ ≈ -0.35
    """
    raw = (
        MODULE_WEIGHTS["tlr"] * score_tlr
        + MODULE_WEIGHTS["hla"] * score_hla
        + MODULE_WEIGHTS["stat"] * score_stat
        + MODULE_WEIGHTS["apoe_peg3"] * score_apoe
    )
    # Center: expected baseline is ~0.65 weighted average
    theta = (raw - 0.65) * 3.0  # Scale to [-2, +2] range typical of IRT
    return round(theta, 4)


def irt_4pl(theta: float, a: float, b: float, c: float = 0.05) -> float:
    """
    4-Parameter Logistic IRT function.

    P(θ) = c + (1 - c) × [1 / (1 + exp(-a × (θ - b)))]
    """
    logit = -a * (theta - b)
    # Clamp to prevent overflow
    logit = max(-500.0, min(500.0, logit))
    return c + (1.0 - c) * (1.0 / (1.0 + math.exp(logit)))


def apply_demographic_adjustments(
    b: float,
    c: float,
    age: int,
    sex: str,
) -> tuple[float, float]:
    """
    Shared demographic adjustment for b (difficulty) and c (lower asymptote).
    Called by run_irt_analysis, compute_protection_probability, and cross_platform_analysis
    to ensure consistent age/sex handling across all IRT calculations.
    Returns (b_adjusted, c_adjusted).
    """
    if age > 65:
        b += 0.30
    elif age < 18:
        b -= 0.10
    if sex == "Male":
        c = max(0.03, c - 0.01)
    return b, c


def compute_protection_probability(
    theta: float,
    vaccine_platform: str = "mRNA",
    age: int = 30,
    sex: str = "Unknown",
) -> float:
    """
    Compute probability of protective immune response using IRT 4PL.
    Standalone wrapper — uses apply_demographic_adjustments for consistency
    with run_irt_analysis. Use run_irt_analysis() for full pipeline reports.
    """
    params = VACCINE_IRT_PARAMS.get(vaccine_platform, VACCINE_IRT_PARAMS["mRNA"])
    a, b, c = params["a"], params["b"], params["c"]
    b, c = apply_demographic_adjustments(b, c, age, sex)
    return irt_4pl(theta, a, b, c)


def compute_confidence_interval(
    theta: float,
    vaccine_platform: str,
    n_simulations: int = 1000,
) -> tuple:
    """Bootstrap-style CI using Gaussian noise on theta."""
    params = VACCINE_IRT_PARAMS[vaccine_platform]
    a, b, c = params["a"], params["b"], params["c"]
    probs = [irt_4pl(theta + np.random.normal(0, 0.1), a, b, c) for _ in range(n_simulations)]
    return (round(float(np.percentile(probs, 2.5)), 4), round(float(np.percentile(probs, 97.5)), 4))


def _dose_recommendation(prob: float, platform: str, has_hla_risk: bool, has_lnp_risk: bool) -> str:
    """Generate dose recommendation based on probability and risk flags."""
    if has_lnp_risk and platform == "mRNA":
        return (
            "CAMBIO DE PLATAFORMA RECOMENDADO: Cambiar de ARNm-LNP a vacuna de subunidad proteica. "
            "El deterioro del aclaramiento lipídico mediado por APOE hace que la plataforma de ARNm-LNP no sea segura."
        )
    if has_hla_risk:
        return (
            "CONTRAINDICACIÓN DETECTADA: Plataforma de vector adenoviral contraindicada (riesgo de VITT). "
            "Utilizar alternativa de ARNm o subunidad proteica. Se recomienda consulta con hematología."
        )
    if prob >= 0.80:
        return "Esquema estándar de 2 dosis. No se requieren modificaciones. Se espera una seroconversión robusta."
    elif prob >= 0.65:
        return (
            "Esquema estándar de 2 dosis con intervalo extendido (6-8 semanas entre dosis). "
            "Se recomienda control de títulos serológicos a las 4 semanas de la segunda dosis."
        )
    elif prob >= 0.45:
        return (
            "Se recomienda una serie primaria de 3 dosis. Considerar formulación con adyuvante (agonista TLR4/7). "
            "Monitoreo de títulos después de cada dosis. Derivación a inmunología especialista si el aumento es menor a 4 veces."
        )
    elif prob >= 0.25:
        return (
            "Se recomienda formulación de dosis alta (2× contenido de antígeno estándar). "
            "Serie extendida de 4 dosis. Considerar sistema adyuvante potenciador de inmunogenicidad (AS01B). "
            "Vigilancia mensual de títulos."
        )
    else:
        return (
            "PREDICCIÓN DE FALLO DE VACUNA: Es poco probable que los protocolos estándar alcancen títulos protectores. "
            "Se recomienda inmunoprofilaxis pasiva (terapia de anticuerpos monoclonales) como protección primaria. "
            "Se pueden considerar protocolos experimentales con adyuvantes en un centro especializado."
        )


def run_irt_analysis(
    score_tlr: float,
    score_hla: float,
    score_stat: float,
    score_apoe: float,
    vaccine_platform: str = "mRNA",
    age: int = 30,
    sex: str = "Unknown",
    has_hla_risk: bool = False,
    has_lnp_risk: bool = False,
    theta_penalty: float = 0.0,
    b_extra: float = 0.0,
) -> IRTResult:
    """Full IRT analysis pipeline for a patient.

    theta_penalty: additive adjustment to θ from immunocompromised module (negative = impaired)
    b_extra:       additive adjustment to b (difficulty) from immunocompromised module (positive = harder)
    """
    theta_genetic = compute_theta(score_tlr, score_hla, score_stat, score_apoe)
    theta = round(theta_genetic + theta_penalty, 4)   # θ_clinical used for IRT calculation

    # Apply b_extra to the platform params before computing probability
    params = VACCINE_IRT_PARAMS[vaccine_platform]
    b_base = params["b"]
    a, b, c = params["a"], b_base + b_extra, params["c"]

    # Demographic adjustments (shared with compute_protection_probability)
    b, c = apply_demographic_adjustments(b, c, age, sex)

    prob = irt_4pl(theta, a, b, c)
    ci = compute_confidence_interval(theta, vaccine_platform)

    # Seroconversion likely if probability > 60%
    seroconversion = prob >= 0.60

    dose_rec = _dose_recommendation(prob, vaccine_platform, has_hla_risk, has_lnp_risk)

    # Human-readable interpretation
    if prob >= 0.80:
        interp = f"ALTA PROBABILIDAD de respuesta protectora ({prob:.1%}). Se recomienda el régimen de vacunación estándar."
    elif prob >= 0.60:
        interp = f"Probabilidad MODERADA-ALTA de protección ({prob:.1%}). La optimización del esquema puede mejorar los resultados."
    elif prob >= 0.40:
        interp = f"Probabilidad MODERADA ({prob:.1%}). Se requiere protocolo intensificado. El monitoreo de títulos es esencial."
    elif prob >= 0.20:
        interp = f"Baja probabilidad de seroconversión ({prob:.1%}). Se requiere estrategia de dosis alta o plataforma alternativa."
    else:
        interp = f"CRÍTICO: Probabilidad de protección muy baja ({prob:.1%}). Es probable que falle la vacuna. Se necesita profilaxis alternativa."

    return IRTResult(
        theta=theta,
        theta_genetic=theta_genetic,
        theta_penalty=theta_penalty,
        probability_protection=round(prob, 4),
        vaccine_platform=vaccine_platform,
        a=a,
        b=b,
        b_base=b_base,
        c=c,
        dose_recommendation=dose_rec,
        confidence_interval=ci,
        seroconversion_likely=seroconversion,
        interpretation=interp,
    )
