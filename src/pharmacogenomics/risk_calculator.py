"""
Risk Calculator: orchestrates all 4 modules + immunocompromised module + IRT
to produce a complete pharmacogenomic report for a single patient.
"""

import logging
from dataclasses import dataclass, asdict
from typing import Optional

from .modules.tlr_module import compute_tlr_score, TLRModuleResult
from .modules.hla_module import compute_hla_score, HLAModuleResult
from .modules.stat_module import compute_stat_score, STATModuleResult
from .modules.apoe_module import compute_apoe_score, APOEModuleResult
from .modules.immunocompromised_module import (
    compute_immunocompromised_score,
    ImmunocompromisedResult,
    SpecialCondition,
    THETA_PENALTY,
    PLATFORM_B_ADJUSTMENT,
)
from .irt_model import run_irt_analysis, IRTResult, compute_theta, irt_4pl
from .cross_platform_analysis import run_cross_platform_irt, CrossPlatformReport

from config import MODULE_WEIGHTS, VACCINE_IRT_PARAMS

logger = logging.getLogger(__name__)


@dataclass
class PatientReport:
    patient_id: str
    age: int
    sex: str
    apoe_genotype: str
    target_vaccine: str

    # Module results
    tlr: TLRModuleResult
    hla: HLAModuleResult
    stat: STATModuleResult
    apoe: APOEModuleResult
    immunocompromised: Optional[ImmunocompromisedResult]

    # IRT result
    irt: IRTResult

    # Cross-platform comparison
    cross_platform: Optional[CrossPlatformReport]

    # Aggregated risk flags
    all_risk_flags: list
    critical_flags: list
    overall_risk_level: str       # LOW / MODERATE / HIGH / CRITICAL
    final_recommendation: str
    special_condition: SpecialCondition = SpecialCondition.NONE

    def to_dict(self) -> dict:
        d = {}
        d["patient_id"] = self.patient_id
        d["age"] = self.age
        d["sex"] = self.sex
        d["apoe_genotype"] = self.apoe_genotype
        d["target_vaccine"] = self.target_vaccine
        d["special_condition"] = self.special_condition.value

        d["module_scores"] = {
            "tlr": {"score": self.tlr.score, "weight": MODULE_WEIGHTS["tlr"]},
            "hla": {"score": self.hla.score, "weight": MODULE_WEIGHTS["hla"]},
            "stat": {"score": self.stat.score, "weight": MODULE_WEIGHTS["stat"]},
            "apoe_peg3": {"score": self.apoe.score, "weight": MODULE_WEIGHTS["apoe_peg3"]},
        }
        d["irt"] = {
            "theta": self.irt.theta,
            "theta_genetic": self.irt.theta_genetic,
            "theta_penalty": self.irt.theta_penalty,
            "probability_protection": self.irt.probability_protection,
            "confidence_interval": self.irt.confidence_interval,
            "seroconversion_likely": self.irt.seroconversion_likely,
            "dose_recommendation": self.irt.dose_recommendation,
            "interpretation": self.irt.interpretation,
            "b_base": self.irt.b_base,
        }
        d["tlr_detail"] = asdict(self.tlr)
        d["hla_detail"] = asdict(self.hla)
        d["stat_detail"] = asdict(self.stat)
        d["apoe_detail"] = asdict(self.apoe)

        if self.immunocompromised and self.immunocompromised.condition != SpecialCondition.NONE:
            d["immunocompromised"] = {
                "condition": self.immunocompromised.condition.value,
                "theta_penalty": self.immunocompromised.theta_penalty,
                "dose_multiplier": self.immunocompromised.dose_multiplier,
                "interpretation": self.immunocompromised.interpretation,
                "monitoring": self.immunocompromised.monitoring_requirements,
                "interactions": self.immunocompromised.interaction_with_genetic_profile,
            }
        else:
            d["immunocompromised"] = None

        if self.cross_platform:
            d["cross_platform"] = [
                {
                    "platform": p.platform,
                    "label": p.label,
                    "probability_protection": p.probability_protection,
                    "seroconversion_likely": p.seroconversion_likely,
                    "rank": p.recommendation_rank,
                    "dose_multiplier": p.dose_multiplier,
                    "contraindicated": p.platform in (self.cross_platform.contraindicated_platforms or []),
                }
                for p in self.cross_platform.platforms
            ]
        else:
            d["cross_platform"] = None

        d["all_risk_flags"] = self.all_risk_flags
        d["critical_flags"] = self.critical_flags
        d["overall_risk_level"] = self.overall_risk_level
        d["final_recommendation"] = self.final_recommendation
        return d


def _classify_risk(
    prob: float,
    has_critical_hla: bool,
    myocarditis_risk: bool,
    lnp_impaired: bool,
) -> str:
    if has_critical_hla:
        return "CRITICAL"
    if prob < 0.25 or (myocarditis_risk and lnp_impaired):
        return "HIGH"
    if prob < 0.55 or myocarditis_risk or lnp_impaired:
        return "MODERATE"
    return "LOW"


def _final_recommendation(
    irt: IRTResult,
    hla: HLAModuleResult,
    stat: STATModuleResult,
    apoe: APOEModuleResult,
    platform: str,
    immunocomp: Optional[ImmunocompromisedResult] = None,
    cross: Optional[CrossPlatformReport] = None,
) -> str:
    lines = []

    # Platform override
    if hla.platform_contraindications.get("adenoviral_vector") and platform == "adenoviral_vector":
        lines.append("CONTRAINDICACIÓN DE PLATAFORMA: Vacuna de vector adenoviral CONTRAINDICADA (riesgo VITT por HLA-DRB1*11:04).")
        lines.append("→ Cambiar a ARNm o subunidad proteica de inmediato.")
    elif apoe.lnp_clearance_profile == "impaired" and platform == "mRNA":
        lines.append("CAMBIO DE PLATAFORMA: ARNm-LNP no recomendado (deterioro del aclaramiento lipídico mediado por APOE).")
        lines.append(f"→ {apoe.platform_recommendation}")
    else:
        lines.append(f"PLATAFORMA: {platform} — {irt.dose_recommendation}")

    # Dose schedule — when the requested platform is contraindicated, show the
    # recommended alternative's probability instead of the contraindicated one.
    prob = irt.probability_protection
    ci_str = f" (IC 95%: {irt.confidence_interval[0]:.1%}–{irt.confidence_interval[1]:.1%})"
    platform_label = ""

    if cross is not None:
        contraindicated = set(cross.contraindicated_platforms or [])
        if platform in contraindicated:
            alternatives = sorted(
                [p for p in cross.platforms if p.platform not in contraindicated],
                key=lambda x: x.recommendation_rank,
            )
            if alternatives:
                best = alternatives[0]
                prob = best.probability_protection
                ci_str = ""
                platform_label = f"  [{best.label}]"

    lines.append(f"\nPROBABILIDAD DE PROTECCIÓN: {prob:.1%}{ci_str}{platform_label}")
    lines.append(f"IRT θ (Capacidad Inmunogénica): {irt.theta:+.3f}")

    # Myocarditis monitoring
    if stat.myocarditis_risk_elevated:
        lines.append("\nMONITORIZACIÓN CARDÍACA: Vigilancia cardíaca post-vacunación (ECG + troponina de alta sensibilidad a las 72h).")

    # Autoimmune monitoring
    if hla.autoimmune_risk_score > 0.4:
        lines.append(f"\nVIGILANCIA AUTOINMUNE: Puntuación de riesgo autoinmune HLA {hla.autoimmune_risk_score:.2f}. "
                     "Monitorizar autoinmunidad órgano-específica (función tiroidea, recuento plaquetario) a las 4 semanas.")

    # Immunocompromised condition addendum
    if immunocomp and immunocomp.condition != SpecialCondition.NONE:
        lines.append(f"\n--- CONDICIÓN ESPECIAL: {immunocomp.condition.value.upper()} ---")
        lines.append(immunocomp.interpretation)
        lines.append(f"Multiplicador de dosis: {immunocomp.dose_multiplier}×")
        if immunocomp.monitoring_requirements:
            lines.append("Monitorización requerida:")
            for req in immunocomp.monitoring_requirements:
                lines.append(f"  • {req}")
        for interaction in immunocomp.interaction_with_genetic_profile:
            lines.append(f"  ⚠ {interaction}")

    # Cross-platform comparison summary
    if cross and len(cross.platforms) > 1:
        lines.append("\n--- COMPARACIÓN ENTRE PLATAFORMAS ---")
        for p in sorted(cross.platforms, key=lambda x: x.recommendation_rank):
            contind = " [CONTRAINDICADA]" if p.platform in (cross.contraindicated_platforms or []) else ""
            lines.append(
                f"  #{p.recommendation_rank} {p.label}: {p.probability_protection:.1%}{contind}"
            )
        lines.append(f"  → Mejor plataforma para este perfil ADN: {cross.best_platform}")

    return "\n".join(lines)


_VALID_PLATFORMS = frozenset(VACCINE_IRT_PARAMS.keys())
_VALID_SEX = frozenset({"Male", "Female", "Other", "Unknown"})


def _validate_inputs(patient_id, age, sex, variants, hla_haplotype, apoe_genotype, target_vaccine):
    """Raise ValueError on invalid inputs before any analysis runs."""
    if not isinstance(patient_id, str) or not patient_id:
        raise ValueError("patient_id must be a non-empty string")
    if not isinstance(age, int) or not (0 < age < 130):
        raise ValueError(f"age must be an integer in (0, 130), got {age!r}")
    if sex not in _VALID_SEX:
        raise ValueError(f"sex must be one of {_VALID_SEX}, got {sex!r}")
    if not isinstance(variants, dict):
        raise ValueError("variants must be a dict")
    if not isinstance(hla_haplotype, dict):
        raise ValueError("hla_haplotype must be a dict")
    if not isinstance(apoe_genotype, str) or not apoe_genotype:
        raise ValueError("apoe_genotype must be a non-empty string")
    if target_vaccine not in _VALID_PLATFORMS:
        raise ValueError(
            f"target_vaccine must be one of {_VALID_PLATFORMS}, got {target_vaccine!r}"
        )


def analyze_patient(
    patient_id: str,
    age: int,
    sex: str,
    variants: dict,
    hla_haplotype: dict,
    apoe_genotype: str,
    target_vaccine: str = "mRNA",
    special_condition: SpecialCondition = SpecialCondition.NONE,
    run_cross_platform: bool = True,
) -> PatientReport:
    """
    Full pharmacogenomic analysis pipeline for one patient.
    Supports normal and immunocompromised patient profiles.
    Returns a complete PatientReport with all module scores and recommendations.
    """
    _validate_inputs(patient_id, age, sex, variants, hla_haplotype, apoe_genotype, target_vaccine)

    # Run all 4 base genetic modules
    tlr = compute_tlr_score(variants)
    hla = compute_hla_score(hla_haplotype, target_platform=target_vaccine)
    stat = compute_stat_score(variants, patient_sex=sex, patient_age=age)
    apoe = compute_apoe_score(variants, apoe_genotype=apoe_genotype)

    # Module 5: immunocompromised condition
    immunocomp = compute_immunocompromised_score(
        condition=special_condition,
        variants=variants,
        hla_haplotype=hla_haplotype,
        target_platform=target_vaccine,
    )

    # Check key risk flags for IRT
    has_lnp_risk = apoe.lnp_clearance_profile == "impaired"
    has_hla_risk = bool(hla.platform_contraindications.get(target_vaccine))

    # Apply immunocompromised θ penalty to IRT b parameter
    theta_penalty = immunocomp.theta_penalty
    b_adj = immunocomp.b_adjustment.get(target_vaccine, 0.0)

    # IRT 4PL analysis (with condition adjustments)
    irt = run_irt_analysis(
        score_tlr=tlr.score,
        score_hla=hla.score,
        score_stat=stat.score,
        score_apoe=apoe.score,
        vaccine_platform=target_vaccine,
        age=age,
        sex=sex,
        has_hla_risk=has_hla_risk,
        has_lnp_risk=has_lnp_risk,
        theta_penalty=theta_penalty,
        b_extra=b_adj,
    )

    # Cross-platform IRT comparison
    cross = None
    if run_cross_platform:
        contraindicated = []
        if has_hla_risk and target_vaccine == "adenoviral_vector":
            contraindicated.append("adenoviral_vector")
        if has_lnp_risk:
            contraindicated.append("mRNA")
        contraindicated += [
            p for p, flag in immunocomp.safety_flags.items()
            if "CONTRAINDICATED" in flag or "contraindicated" in flag
        ]
        cross = run_cross_platform_irt(
            patient_id=patient_id,
            score_tlr=tlr.score,
            score_hla=hla.score,
            score_stat=stat.score,
            score_apoe=apoe.score,
            special_condition=special_condition,
            age=age,
            sex=sex,
            immunocompromised_result=immunocomp,
            contraindicated_platforms=list(set(contraindicated)),
        )

    # Aggregate all risk flags
    all_flags = (tlr.risk_flags + hla.risk_flags + stat.risk_flags
                 + apoe.risk_flags + immunocomp.risk_flags)
    critical_flags = [f for f in all_flags if any(
        kw in f.upper() for kw in [
            "CRITICAL", "CONTRAINDICATION", "CONTRAINDICATED", "SYNERGISTIC RISK", "CYTOKINE STORM",
            "CONTRAINDICACIÓN", "CONTRAINDICADO", "SINÉRGICO", "TORMENTA DE CITOCINAS",
        ]
    )]

    risk_level = _classify_risk(
        prob=irt.probability_protection,
        has_critical_hla=bool(critical_flags),
        myocarditis_risk=stat.myocarditis_risk_elevated,
        lnp_impaired=has_lnp_risk,
    )
    # Upgrade risk level for severe immunosuppression
    if special_condition in (SpecialCondition.HIV_SEVERE, SpecialCondition.BMT_RECENT,
                             SpecialCondition.CANCER_ACTIVE, SpecialCondition.SOLID_ORGAN_TRANSPLANT):
        if risk_level == "LOW":
            risk_level = "MODERATE"
        elif risk_level == "MODERATE":
            risk_level = "HIGH"

    recommendation = _final_recommendation(irt, hla, stat, apoe, target_vaccine,
                                            immunocomp=immunocomp, cross=cross)

    return PatientReport(
        patient_id=patient_id,
        age=age,
        sex=sex,
        apoe_genotype=apoe_genotype,
        target_vaccine=target_vaccine,
        special_condition=special_condition,
        tlr=tlr,
        hla=hla,
        stat=stat,
        apoe=apoe,
        immunocompromised=immunocomp,
        irt=irt,
        cross_platform=cross,
        all_risk_flags=all_flags,
        critical_flags=critical_flags,
        overall_risk_level=risk_level,
        final_recommendation=recommendation,
    )
