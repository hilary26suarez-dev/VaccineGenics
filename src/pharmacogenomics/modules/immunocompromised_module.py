"""
Module 5: Special Clinical Conditions — Immunocompromised Patients

Evaluates how radiation exposure, cancer (active/remission), HIV/AIDS,
solid-organ transplant, and severe autoimmune therapy alter vaccine
immunogenicity and platform safety.

This module does NOT carry an independent percentage weight in the θ formula.
Instead it applies a CONDITIONAL PENALTY on θ and modifies the b (difficulty)
parameter of the IRT vaccine-platform parameters.

Biological rationale:
  - Radiation/chemo → lymphopenia + bone marrow suppression → reduced TLR innate
    signaling and severely reduced adaptive (B/T cell) response.
  - HIV (CD4 < 200) → depletion of helper T cells → collapsed antibody response.
    ARNm vaccines in HIV: meta-analyses show ~40% lower peak NAb vs HIV-neg controls.
  - Transplant (calcineurin inhibitors) → T-cell anergy → poor HLA-mediated
    antigen presentation despite intact genetic HLA haplotype.
  - STING pathway (activated by radiation / innate pattern recognition of dsDNA) →
    paradoxically can enhance innate sensing of LNP/ARNm but also drives interferonopathy.
  - Cancer + LOH at HLA loci (common in solid tumors) → effectively impairs the
    individual's actual antigen presentation even with "protective" germline HLA alleles.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ConditionSeverity(str, Enum):
    NONE     = "none"
    MILD     = "mild"
    MODERATE = "moderate"
    SEVERE   = "severe"
    CRITICAL = "critical"


class SpecialCondition(str, Enum):
    NONE               = "none"
    RADIATION_EXPOSURE = "radiation_exposure"
    CANCER_ACTIVE      = "cancer_active_treatment"
    CANCER_REMISSION   = "cancer_remission"
    HIV_CONTROLLED     = "hiv_controlled"      # CD4 > 500 + ART
    HIV_MODERATE       = "hiv_moderate"        # CD4 200-500
    HIV_SEVERE         = "hiv_severe"          # CD4 < 200
    SOLID_ORGAN_TRANSPLANT = "solid_organ_transplant"
    BMT_RECENT         = "bone_marrow_transplant_recent"   # < 2 years
    BMT_ESTABLISHED    = "bone_marrow_transplant_established"
    AUTOIMMUNE_BIOLOGICS = "autoimmune_on_biologics"   # anti-TNF, anti-IL6, etc.
    AUTOIMMUNE_STEROIDS  = "autoimmune_on_steroids"    # pred >= 20 mg/day


# θ penalty per condition (applied additively to computed θ from genetic modules)
# Negative = impairs immunogenic capacity
THETA_PENALTY = {
    SpecialCondition.NONE:                    0.00,
    SpecialCondition.RADIATION_EXPOSURE:     -0.45,   # Myelosuppression
    SpecialCondition.CANCER_ACTIVE:          -0.60,   # Chemo-induced lymphopenia
    SpecialCondition.CANCER_REMISSION:       -0.20,   # Residual immune deficit
    SpecialCondition.HIV_CONTROLLED:         -0.15,   # CD4>500 + ART: near normal
    SpecialCondition.HIV_MODERATE:           -0.40,   # CD4 200-500
    SpecialCondition.HIV_SEVERE:             -0.80,   # CD4<200: severe deficit
    SpecialCondition.SOLID_ORGAN_TRANSPLANT: -0.55,   # CNI + steroids
    SpecialCondition.BMT_RECENT:             -0.70,   # Reconstituting immune system
    SpecialCondition.BMT_ESTABLISHED:        -0.25,   # >2 years: partial recovery
    SpecialCondition.AUTOIMMUNE_BIOLOGICS:   -0.35,   # anti-TNF/IL-6 reduce response
    SpecialCondition.AUTOIMMUNE_STEROIDS:    -0.30,   # Systemic corticosteroids
}

# Platform-specific b (difficulty) adjustments for immunocompromised
# Positive = vaccine "harder" for this patient → lower P(protection)
PLATFORM_B_ADJUSTMENT = {
    SpecialCondition.NONE: {
        "mRNA": 0.0, "adenoviral_vector": 0.0, "protein_subunit": 0.0,
    },
    SpecialCondition.RADIATION_EXPOSURE: {
        "mRNA": +0.20,           # LNP uptake affected by radiation-damaged epithelium
        "adenoviral_vector": +0.15,
        "protein_subunit": +0.30,  # Requires intact B-cell response
    },
    SpecialCondition.CANCER_ACTIVE: {
        "mRNA": +0.25,
        "adenoviral_vector": +0.35,  # Adenoviral vector may reactivate latent infections
        "protein_subunit": +0.40,
    },
    SpecialCondition.CANCER_REMISSION: {
        "mRNA": +0.10,
        "adenoviral_vector": +0.10,
        "protein_subunit": +0.15,
    },
    SpecialCondition.HIV_CONTROLLED: {
        "mRNA": +0.05,
        "adenoviral_vector": +0.10,
        "protein_subunit": +0.10,
    },
    SpecialCondition.HIV_MODERATE: {
        "mRNA": +0.20,           # mRNA still more efficacious than alternatives in HIV
        "adenoviral_vector": +0.30,
        "protein_subunit": +0.25,
    },
    SpecialCondition.HIV_SEVERE: {
        "mRNA": +0.50,
        "adenoviral_vector": +0.60,  # Risk of adenoviral replication in severe immunosuppression
        "protein_subunit": +0.55,
    },
    SpecialCondition.SOLID_ORGAN_TRANSPLANT: {
        "mRNA": +0.30,
        "adenoviral_vector": +0.45,  # Risk of graft rejection driven by pro-inflammatory response
        "protein_subunit": +0.35,
    },
    SpecialCondition.BMT_RECENT: {
        "mRNA": +0.40,           # High-dose schedule needed
        "adenoviral_vector": +0.55,  # Pre-existing anti-Ad vector immunity from conditioning
        "protein_subunit": +0.40,
    },
    SpecialCondition.BMT_ESTABLISHED: {
        "mRNA": +0.15,
        "adenoviral_vector": +0.20,
        "protein_subunit": +0.20,
    },
    SpecialCondition.AUTOIMMUNE_BIOLOGICS: {
        "mRNA": +0.15,
        "adenoviral_vector": +0.20,
        "protein_subunit": +0.25,
    },
    SpecialCondition.AUTOIMMUNE_STEROIDS: {
        "mRNA": +0.20,
        "adenoviral_vector": +0.25,
        "protein_subunit": +0.30,
    },
}

# Safety flags per condition × platform
SAFETY_FLAGS = {
    SpecialCondition.HIV_SEVERE: {
        "adenoviral_vector": "RIESGO: Vector adenoviral contraindicado con CD4<200 — posible replicación viral.",
    },
    SpecialCondition.BMT_RECENT: {
        "adenoviral_vector": "RIESGO: Vacunas vivas/vector viral contraindicadas <6 meses post-TMO.",
    },
    SpecialCondition.SOLID_ORGAN_TRANSPLANT: {
        "adenoviral_vector": "PRECAUCIÓN: Vectores adenovirales pueden desencadenar respuesta inflamatoria del aloinjerto.",
        "mRNA": "NOTA: Plataforma ARNm preferida en trasplante — menor inflamación sistémica vs vector.",
    },
    SpecialCondition.CANCER_ACTIVE: {
        "adenoviral_vector": "PRECAUCIÓN: Cáncer activo — evitar vectores virales inmunoestimulantes si neutrófilos < 1000/μL.",
    },
}

# Recommended dose multiplier per condition
DOSE_MULTIPLIER = {
    SpecialCondition.NONE:                    1.0,
    SpecialCondition.RADIATION_EXPOSURE:      1.5,   # 50% higher dose
    SpecialCondition.CANCER_ACTIVE:           2.0,   # Double-dose or 3-dose primary series
    SpecialCondition.CANCER_REMISSION:        1.5,
    SpecialCondition.HIV_CONTROLLED:          1.0,
    SpecialCondition.HIV_MODERATE:            1.5,
    SpecialCondition.HIV_SEVERE:              2.0,
    SpecialCondition.SOLID_ORGAN_TRANSPLANT:  2.0,
    SpecialCondition.BMT_RECENT:              2.0,
    SpecialCondition.BMT_ESTABLISHED:         1.5,
    SpecialCondition.AUTOIMMUNE_BIOLOGICS:    1.5,
    SpecialCondition.AUTOIMMUNE_STEROIDS:     1.5,
}

# Monitoring requirements
MONITORING_REQUIREMENTS = {
    SpecialCondition.RADIATION_EXPOSURE: [
        "Hemograma completo (CBC) antes de cada dosis vacunal",
        "Posponer si ANC < 500/μL",
        "Título serológico a las 4 y 12 semanas",
    ],
    SpecialCondition.CANCER_ACTIVE: [
        "Consulta con inmunología antes de la vacunación",
        "Posponer hasta recuperación del nadir (ANC > 1000/μL)",
        "Título serológico a las 4 semanas; re-dosis si titer sub-protector",
        "Evitar vacunas vivas atenuadas",
    ],
    SpecialCondition.HIV_SEVERE: [
        "Iniciar TAR antes de la vacunación si no está en tratamiento",
        "Repetir vacunación tras reconstitución CD4 (> 200/μL)",
        "Monitorización de carga viral VIH",
        "Vigilancia serológica mensual durante 3 meses post-vacuna",
    ],
    SpecialCondition.SOLID_ORGAN_TRANSPLANT: [
        "Co-manejo cardiología/nefrología/hepatología",
        "Monitorizar niveles de tacrolimus/ciclosporina post-vacuna (la fiebre puede alterar la cinética)",
        "Título serológico a las 4 y 8 semanas; se recomienda esquema de 3 dosis",
        "Laboratorio de función del injerto 2 semanas post-vacuna",
    ],
    SpecialCondition.BMT_RECENT: [
        "Reiniciar esquema vacunal >3 meses post-TMO para plataformas ARNm",
        "Reiniciar todas las vacunas de la infancia según guías EBMT 2022",
        "Hemograma mensual",
        "Evitar todas las vacunas vivas durante 2 años post-TMO",
    ],
}


@dataclass
class ImmunocompromisedResult:
    condition: SpecialCondition
    theta_penalty: float
    b_adjustment: dict        # per platform
    dose_multiplier: float
    safety_flags: dict        # per platform
    monitoring_requirements: list
    interaction_with_genetic_profile: list   # gene × condition interactions
    interpretation: str
    risk_flags: list


def _detect_gene_condition_interactions(
    condition: SpecialCondition,
    variants: dict,
    hla_haplotype: dict,
) -> list:
    """Identify synergistic risks between special conditions and genetic variants."""
    interactions = []

    # TLR7 (X-linked) LOF + HIV → compounded innate immunity deficit
    if "rs179008" in variants and condition in (SpecialCondition.HIV_MODERATE, SpecialCondition.HIV_SEVERE):
        interactions.append(
            "RIESGO SINÉRGICO: TLR7 rs179008 LOF + VIH — el déficit de TLR7 ligado al X agrava "
            "el deterioro inmune innato por VIH. Reconocimiento de vacuna ssRNA severamente reducido."
        )

    # TLR4 LOF + cancer active → double TLR-pathway hit
    if "rs4986790" in variants and condition == SpecialCondition.CANCER_ACTIVE:
        interactions.append(
            "RIESGO SINÉRGICO: TLR4 Asp299Gly LOF + quimioterapia activa — "
            "señalización NF-κB suprimida tanto por la variante genética como por la linfopenia inducida por fármacos."
        )

    # APOE ε4 + radiation → LNP delivery in irradiated tissue
    if "rs429358" in variants and condition == SpecialCondition.RADIATION_EXPOSURE:
        interactions.append(
            "RIESGO DE ENTREGA LNP: APOE ε4 + tejido de inyección dañado por radiación — "
            "el aclaramiento de LNP del tejido irradiado está aún más comprometido. "
            "Preferir inyección en miembro contralateral y plataforma de subunidad proteica."
        )

    # IL-6 hyperexpressor + cancer active → cytokine storm risk
    if "rs1800795" in variants:
        zygosity = variants["rs1800795"].get("zygosity", "")
        if zygosity == "homozygous" and condition in (SpecialCondition.CANCER_ACTIVE, SpecialCondition.BMT_RECENT):
            interactions.append(
                "RIESGO DE TORMENTA DE CITOCINAS: IL-6 rs1800795 GG homocigoto + estado inmunosuprimido — "
                "rebote hiperinflamatorio paradójico al administrar la vacuna durante la fase de reconstitución inmune. "
                "Puede estar indicado tocilizumab profiláctico."
            )

    # HLA-DRB1*11:04 + transplant → VITT risk even without adenoviral vector
    hla_alleles = []
    for cls in hla_haplotype.values():
        for locus_alleles in cls.values():
            if isinstance(locus_alleles, list):
                hla_alleles.extend(locus_alleles)
    if "HLA-DRB1*11:04" in hla_alleles and condition == SpecialCondition.SOLID_ORGAN_TRANSPLANT:
        interactions.append(
            "RIESGO TROMBÓTICO: HLA-DRB1*11:04 + trasplante de órgano sólido — "
            "riesgo elevado de formación de anticuerpos anti-PF4 en pacientes trasplantados con anticoagulación. "
            "Evitar estrictamente la plataforma de vector adenoviral. Requiere co-manejo con hematología."
        )

    return interactions


def compute_immunocompromised_score(
    condition: SpecialCondition,
    variants: dict,
    hla_haplotype: dict,
    target_platform: str = "mRNA",
) -> ImmunocompromisedResult:
    """
    Evaluate the immunocompromised condition impact on vaccine response.
    Returns θ penalty and platform-specific b adjustments.
    """
    theta_penalty = THETA_PENALTY[condition]
    b_adj = PLATFORM_B_ADJUSTMENT.get(condition, {})
    dose_mult = DOSE_MULTIPLIER[condition]
    safety = SAFETY_FLAGS.get(condition, {})
    monitoring = MONITORING_REQUIREMENTS.get(condition, [])
    interactions = _detect_gene_condition_interactions(condition, variants, hla_haplotype)

    risk_flags = list(interactions)
    for platform, flag in safety.items():
        risk_flags.append(f"[{platform.upper()}] {flag}")

    # Interpretation
    if condition == SpecialCondition.NONE:
        interpretation = "Sin condición inmunocomprometedora detectada. Se aplica protocolo de vacunación estándar."
    elif abs(theta_penalty) >= 0.60:
        interpretation = (
            f"INMUNOSUPRESIÓN SEVERA ({condition.value}): penalización θ {theta_penalty:+.2f}. "
            f"Los protocolos de vacunación estándar probablemente fallarán. "
            f"Multiplicador de dosis: {dose_mult}×. Se requiere inmunización guiada por especialista."
        )
    elif abs(theta_penalty) >= 0.35:
        interpretation = (
            f"INMUNOSUPRESIÓN MODERADA ({condition.value}): penalización θ {theta_penalty:+.2f}. "
            f"Se recomienda esquema intensificado ({dose_mult}× dosis equivalente) con monitorización de títulos."
        )
    else:
        interpretation = (
            f"INMUNOSUPRESIÓN LEVE ({condition.value}): penalización θ {theta_penalty:+.2f}. "
            f"Esquema estándar con control de títulos post-vacuna a las 4 semanas."
        )

    return ImmunocompromisedResult(
        condition=condition,
        theta_penalty=theta_penalty,
        b_adjustment=b_adj,
        dose_multiplier=dose_mult,
        safety_flags=safety,
        monitoring_requirements=monitoring,
        interaction_with_genetic_profile=interactions,
        interpretation=interpretation,
        risk_flags=risk_flags,
    )
