"""
Synthetic patient cohort generator.

Generates biologically realistic synthetic patients by sampling from
population-frequency-weighted genetic variant distributions.

Each patient has:
  - Unique ID (P-XXXX)
  - Demographics (age, sex)
  - Genetic profile: dict of gene → list of variant IDs/rsIDs present
  - HLA haplotype (class I and class II)
  - Vaccination history
"""

import json
import random
import logging
import os
import uuid
from dataclasses import dataclass, field, asdict
from typing import Optional

import requests
from config import COHORT_SIZE, RANDOM_SEED, PATIENTS_DIR, CLUSTAN_OMEGA_ENDPOINT, CLUSTAN_OMEGA_ENABLED
from pharmacogenomics.modules.immunocompromised_module import SpecialCondition

logger = logging.getLogger(__name__)

# HLA allele frequencies in general population
HLA_CLASS_I_POOL = {
    "HLA-A*02:01": 0.28,  "HLA-A*01:01": 0.16,  "HLA-A*03:01": 0.14,
    "HLA-A*24:02": 0.12,  "HLA-A*11:01": 0.10,  "HLA-A*68:01": 0.05,
    "HLA-A*23:01": 0.04,  "HLA-A*29:01": 0.03,  "HLA-A*32:01": 0.04,
    "HLA-A*31:01": 0.04,
}
HLA_B_POOL = {
    "HLA-B*07:02": 0.12,  "HLA-B*08:01": 0.11,  "HLA-B*44:02": 0.10,
    "HLA-B*35:01": 0.08,  "HLA-B*40:01": 0.07,  "HLA-B*15:01": 0.07,
    "HLA-B*51:01": 0.06,  "HLA-B*18:01": 0.06,  "HLA-B*57:01": 0.05,
    "HLA-B*35:03": 0.04,  "HLA-B*49:01": 0.03,  "HLA-B*53:01": 0.04,
    "HLA-C*07:01": 0.12,  "HLA-C*07:02": 0.10,  "HLA-C*04:01": 0.09,
    "HLA-C*03:04": 0.08,  "HLA-C*06:02": 0.07,  "HLA-C*08:02": 0.06,
}
HLA_CLASS_II_POOL = {
    "HLA-DRB1*01:01": 0.10, "HLA-DRB1*03:01": 0.12, "HLA-DRB1*04:01": 0.10,
    "HLA-DRB1*07:01": 0.11, "HLA-DRB1*11:01": 0.09, "HLA-DRB1*13:01": 0.07,
    "HLA-DRB1*15:01": 0.13, "HLA-DRB1*11:04": 0.03, "HLA-DRB1*01:03": 0.04,
    "HLA-DQB1*02:01": 0.12, "HLA-DQB1*03:01": 0.14, "HLA-DQB1*05:01": 0.10,
    "HLA-DQB1*06:02": 0.08, "HLA-DQB1*06:03": 0.06, "HLA-DQB1*04:02": 0.05,
}

# Key variant rsIDs with population frequencies for random sampling.
# IL-6 promoter variants (rs1800795/96/97) are in moderate LD and are sampled
# via _sample_il6_haplotype() below — they are EXCLUDED from independent HWE sampling.
VARIANT_FREQUENCIES = {
    # TLR pathway
    "rs4986790": 0.07,   # TLR4 Asp299Gly
    "rs4986791": 0.05,   # TLR4 Thr399Ile
    "rs179008":  0.25,   # TLR7 Gln11Leu (X-linked)
    "rs5743836": 0.15,   # TLR9 T-1237C promoter
    "rs352140":  0.19,   # TLR9 +2848 A>G
    "rs2070788": 0.28,   # TMPRSS2 A>G

    # STAT pathway (non-IL6 — sampled independently)
    "rs1137578":  0.08,  # STAT3
    "rs12233781": 0.11,  # STAT1

    # APOE / lipid
    "rs429358": 0.14,    # APOE epsilon4 allele
    "rs7412":   0.07,    # APOE epsilon2 allele
}

# ── IL-6 promoter haplotype block (chr7:22766767–22771527, ~5 kb) ──────────
# rs1800795 (-174G>C), rs1800796 (-572G>C), rs1800797 (-597G>A) are in moderate
# LD (r²≈0.4–0.6). Population-specific haplotype frequencies from:
#   - CEU/EUR: Fishman et al. (1998); HapMap CEU
#   - AFR: 1000 Genomes YRI + dbSNP gnomAD v4 African/African-American
#   - EAS: 1000 Genomes CHB+JPT; gnomAD v4 East Asian
#   - SAS: 1000 Genomes PJL+BEB; gnomAD v4 South Asian
#   - LAT: 1000 Genomes PEL+MXL (admixed); gnomAD v4 Latino
#
# Each tuple = (rs1800795_effect, rs1800796_effect, rs1800797_effect, freq)
# True = effect allele present (higher IL-6 promoter activity in the STAT module context)
_IL6_HAPLOTYPES_BY_POP: dict[str, list] = {
    "CEU": [  # European — G allele freq rs1800795 ≈ 0.62
        (True,  False, True,  0.34),  # High IL-6 (rs795+, rs797+)
        (False, False, False, 0.26),  # Reference
        (True,  False, False, 0.21),  # Intermediate
        (False, True,  True,  0.12),  # rs796+ haplotype
        (True,  True,  True,  0.07),  # Triple (rare)
    ],
    "AFR": [  # African — G allele freq rs1800795 ≈ 0.45 (lower than EUR)
        (True,  False, True,  0.22),
        (False, False, False, 0.33),  # Reference more common in AFR
        (True,  False, False, 0.25),
        (False, True,  True,  0.15),
        (True,  True,  True,  0.05),
    ],
    "EAS": [  # East Asian — G allele freq rs1800795 ≈ 0.76 (highest across pops)
        (True,  False, True,  0.48),  # High IL-6 most prevalent
        (False, False, False, 0.18),
        (True,  False, False, 0.20),
        (False, True,  True,  0.10),
        (True,  True,  True,  0.04),
    ],
    "SAS": [  # South Asian — G allele freq rs1800795 ≈ 0.66
        (True,  False, True,  0.38),
        (False, False, False, 0.24),
        (True,  False, False, 0.22),
        (False, True,  True,  0.11),
        (True,  True,  True,  0.05),
    ],
    "LAT": [  # Latino (admixed EUR+AMR+AFR) — intermediate frequencies
        (True,  False, True,  0.30),
        (False, False, False, 0.28),
        (True,  False, False, 0.23),
        (False, True,  True,  0.13),
        (True,  True,  True,  0.06),
    ],
}
_IL6_RSIDS = ("rs1800795", "rs1800796", "rs1800797")

# Map SyntheticPatient ethnicity labels → population code
_ETHNICITY_TO_POP = {
    "European":    "CEU",
    "African":     "AFR",
    "East Asian":  "EAS",
    "South Asian": "SAS",
    "Latino":      "LAT",
    "Mixed":       "CEU",  # CEU as default for mixed/other
}


def _sample_il6_haplotype(population: str = "CEU") -> dict:
    """
    Sample IL-6 promoter genotype using haplotype-aware LD model (diploid).
    Uses population-specific haplotype tables to model ancestry-dependent
    allele frequency differences at rs1800795/96/97.
    Returns a partial variant dict for the 3 IL-6 rsIDs.
    """
    haplotypes = _IL6_HAPLOTYPES_BY_POP.get(population, _IL6_HAPLOTYPES_BY_POP["CEU"])
    freqs = [h[3] for h in haplotypes]
    total = sum(freqs)
    norm = [f / total for f in freqs]

    # Draw 2 haplotypes independently (phase-unknown diploid)
    hap_a = random.choices(haplotypes, weights=norm)[0]
    hap_b = random.choices(haplotypes, weights=norm)[0]

    result = {}
    for i, rsid in enumerate(_IL6_RSIDS):
        allele_a = hap_a[i]
        allele_b = hap_b[i]
        copies = int(allele_a) + int(allele_b)
        if copies > 0:
            result[rsid] = {
                "copies": copies,
                "zygosity": "homozygous" if copies == 2 else "heterozygous",
            }
    return result

VACCINE_PLATFORMS = ["mRNA", "adenoviral_vector", "protein_subunit"]
VACCINE_PLATFORM_SET = set(VACCINE_PLATFORMS)

PREVIOUS_VACCINES = ["COVID-19", "Influenza", "Hepatitis B", "MMR", "Tdap", "HPV"]


def _weighted_sample(pool: dict, k: int = 2) -> list[str]:
    """Sample k alleles weighted by their population frequency."""
    alleles = list(pool.keys())
    weights = list(pool.values())
    total = sum(weights)
    norm_weights = [w / total for w in weights]
    return random.choices(alleles, weights=norm_weights, k=k)


def _sample_variants(ethnicity: str = "European") -> dict[str, list]:
    """Sample variant presence/absence for each gene based on population AF.

    IL-6 promoter variants are sampled via _sample_il6_haplotype() (LD-aware,
    population-stratified) instead of independent Hardy-Weinberg to avoid
    co-occurrence inflation and model ancestry-specific allele frequencies.
    All other variants use standard HWE diploid sampling.
    """
    profile = {}

    # Independent HWE sampling for non-LD variants
    for rsid, freq in VARIANT_FREQUENCIES.items():
        p_hom = freq ** 2
        p_het = 2 * freq * (1 - freq)
        r = random.random()
        if r < p_hom:
            copies = 2
        elif r < p_hom + p_het:
            copies = 1
        else:
            copies = 0
        if copies > 0:
            profile[rsid] = {"copies": copies, "zygosity": "homozygous" if copies == 2 else "heterozygous"}

    # LD-aware IL-6 promoter block with population-specific haplotype frequencies
    population = _ETHNICITY_TO_POP.get(ethnicity, "CEU")
    profile.update(_sample_il6_haplotype(population))

    return profile


def _sample_hla_haplotype() -> dict:
    """Sample a realistic HLA haplotype."""
    return {
        "class_I": {
            "HLA-A": _weighted_sample(HLA_CLASS_I_POOL, k=2),
            "HLA-B": _weighted_sample(HLA_B_POOL, k=2),
        },
        "class_II": {
            "HLA-DRB1": _weighted_sample(HLA_CLASS_II_POOL, k=2),
            "HLA-DQB1": _weighted_sample(HLA_CLASS_II_POOL, k=2),
        },
    }


def _determine_apoe_genotype(variants: dict) -> str:
    """Infer APOE isoform from rs429358 and rs7412."""
    has_e4 = "rs429358" in variants  # C allele at rs429358
    has_e2 = "rs7412" in variants    # T allele at rs7412

    if has_e4 and has_e2:
        return "ε2/ε4"
    if has_e4:
        return "ε3/ε4" if variants["rs429358"]["copies"] == 1 else "ε4/ε4"
    if has_e2:
        return "ε2/ε3" if variants["rs7412"]["copies"] == 1 else "ε2/ε2"
    return "ε3/ε3"


@dataclass
class SyntheticPatient:
    patient_id: str
    age: int
    sex: str
    ethnicity: str
    weight_kg: float
    bmi: float
    comorbidities: list
    variants: dict          # rsID → {copies, zygosity}
    hla_haplotype: dict
    apoe_genotype: str
    vaccination_history: list
    target_vaccine: str     # Platform to be recommended
    special_condition: str = SpecialCondition.NONE.value  # immunocompromised state

    def to_dict(self) -> dict:
        return asdict(self)

    def validate(self) -> bool:
        if not isinstance(self.patient_id, str) or not self.patient_id:
            raise ValueError(f"Invalid patient_id: {self.patient_id}")
        if not isinstance(self.age, int) or self.age <= 0:
            raise ValueError(f"Invalid age for {self.patient_id}: {self.age}")
        if self.sex not in {"Male", "Female", "Other"}:
            raise ValueError(f"Invalid sex for {self.patient_id}: {self.sex}")
        if not isinstance(self.variants, dict):
            raise ValueError(f"Invalid variants profile for {self.patient_id}")
        if not isinstance(self.hla_haplotype, dict):
            raise ValueError(f"Invalid HLA haplotype for {self.patient_id}")
        if not isinstance(self.apoe_genotype, str) or not self.apoe_genotype:
            raise ValueError(f"Invalid APOE genotype for {self.patient_id}: {self.apoe_genotype}")
        if not isinstance(self.target_vaccine, str) or self.target_vaccine not in VACCINE_PLATFORM_SET:
            self.target_vaccine = "mRNA"
        if not isinstance(self.vaccination_history, list):
            raise ValueError(f"Invalid vaccination_history for {self.patient_id}")
        # Coerce special_condition to string value if it's an enum
        if isinstance(self.special_condition, SpecialCondition):
            self.special_condition = self.special_condition.value
        return True

    @classmethod
    def from_dict(cls, d: dict) -> "SyntheticPatient":
        data = dict(d)
        data.setdefault("target_vaccine", "mRNA")
        data.setdefault("special_condition", SpecialCondition.NONE.value)
        # Deserialize enum value string back to string (keep as string for JSON compatibility)
        patient = cls(**data)
        patient.validate()
        return patient


ETHNICITIES = ["European", "African", "Latino", "East Asian", "South Asian", "Mixed"]
ETHNICITY_WEIGHTS = [0.35, 0.18, 0.20, 0.12, 0.10, 0.05]

COMORBIDITIES = ["None", "Hypertension", "Diabetes Type 2", "Obesity", "Asthma",
                 "Autoimmune disease", "Cardiac disease", "Immunocompromised"]
COMORBIDITY_WEIGHTS = [0.55, 0.15, 0.10, 0.08, 0.05, 0.04, 0.02, 0.01]

# Realistic population prevalence of immunocompromised states (~10% of cohort overall)
_SPECIAL_CONDITIONS = [
    SpecialCondition.NONE,
    SpecialCondition.RADIATION_EXPOSURE,
    SpecialCondition.CANCER_ACTIVE,
    SpecialCondition.CANCER_REMISSION,
    SpecialCondition.HIV_CONTROLLED,
    SpecialCondition.HIV_MODERATE,
    SpecialCondition.HIV_SEVERE,
    SpecialCondition.SOLID_ORGAN_TRANSPLANT,
    SpecialCondition.BMT_RECENT,
    SpecialCondition.BMT_ESTABLISHED,
    SpecialCondition.AUTOIMMUNE_BIOLOGICS,
    SpecialCondition.AUTOIMMUNE_STEROIDS,
]
_SPECIAL_CONDITION_WEIGHTS = [
    0.895,   # NONE — healthy majority
    0.010,   # RADIATION_EXPOSURE
    0.012,   # CANCER_ACTIVE
    0.015,   # CANCER_REMISSION
    0.010,   # HIV_CONTROLLED
    0.005,   # HIV_MODERATE
    0.003,   # HIV_SEVERE
    0.008,   # SOLID_ORGAN_TRANSPLANT
    0.003,   # BMT_RECENT
    0.004,   # BMT_ESTABLISHED
    0.018,   # AUTOIMMUNE_BIOLOGICS
    0.017,   # AUTOIMMUNE_STEROIDS
]


def _validate_clustan_omega_url(url: str) -> bool:
    """Reject obviously dangerous URLs to mitigate SSRF risk."""
    from urllib.parse import urlparse
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        host = parsed.hostname or ""
        # Block internal/loopback/link-local targets
        if host in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
            return False
        if host.startswith("192.168.") or host.startswith("10.") or host.startswith("172."):
            return False
        if host == "169.254.169.254":  # AWS metadata endpoint
            return False
        return True
    except Exception:
        return False


def _simulate_patient_with_clustan_omega(seed: dict) -> Optional[SyntheticPatient]:
    """Optional integration with Clustan Omega for improved synthetic genetic simulation."""
    if not CLUSTAN_OMEGA_ENABLED:
        return None

    if not _validate_clustan_omega_url(CLUSTAN_OMEGA_ENDPOINT):
        logger.warning("CLUSTAN_OMEGA_ENDPOINT failed SSRF validation — skipping external call.")
        return None

    payload = {
        "seed_patient_id": seed["patient_id"],
        "age": seed["age"],
        "sex": seed["sex"],
        "ethnicity": seed["ethnicity"],
        "bmi": seed["bmi"],
        "comorbidities": seed["comorbidities"],
        "variants": seed["variants"],
        "hla_haplotype": seed["hla_haplotype"],
        "apoe_genotype": seed["apoe_genotype"],
        "target_vaccine": seed["target_vaccine"],
    }

    try:
        response = requests.post(CLUSTAN_OMEGA_ENDPOINT, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, dict):
            logger.warning("Clustan Omega response not JSON object; falling back to local generator.")
            return None

        return SyntheticPatient(
            patient_id=seed["patient_id"],
            age=data.get("age", seed["age"]),
            sex=data.get("sex", seed["sex"]),
            ethnicity=data.get("ethnicity", seed["ethnicity"]),
            weight_kg=data.get("weight_kg", seed["weight_kg"]),
            bmi=data.get("bmi", seed["bmi"]),
            comorbidities=data.get("comorbidities", seed["comorbidities"]),
            variants=data.get("variants", seed["variants"]),
            hla_haplotype=data.get("hla_haplotype", seed["hla_haplotype"]),
            apoe_genotype=data.get("apoe_genotype", seed["apoe_genotype"]),
            vaccination_history=data.get("vaccination_history", seed["vaccination_history"]),
            target_vaccine=data.get("target_vaccine", seed["target_vaccine"]),
            special_condition=data.get("special_condition", seed.get("special_condition", SpecialCondition.NONE.value)),
        )
    except Exception as exc:
        logger.warning("Clustan Omega simulation failed: %s", exc)
        return None


def generate_patient(patient_num: int) -> SyntheticPatient:
    """Generate a single synthetic patient."""
    age = random.randint(12, 85)
    sex = random.choice(["Male", "Female"])
    ethnicity = random.choices(ETHNICITIES, weights=ETHNICITY_WEIGHTS)[0]
    bmi = round(random.gauss(26.5, 5.0), 1)
    bmi = max(16.0, min(45.0, bmi))

    # Ethnicity must be determined before variant sampling for IL-6 LD stratification
    variants = _sample_variants(ethnicity)
    hla = _sample_hla_haplotype()
    apoe = _determine_apoe_genotype(variants)

    n_previous = random.choices([0, 1, 2, 3, 4], weights=[0.05, 0.15, 0.30, 0.30, 0.20])[0]
    vacc_history = random.sample(PREVIOUS_VACCINES, min(n_previous, len(PREVIOUS_VACCINES)))

    n_comorbidities = random.choices([0, 1, 2], weights=[0.60, 0.30, 0.10])[0]
    comorbidities_pool = COMORBIDITIES[1:]  # exclude "None"
    comorbidities = random.sample(comorbidities_pool, min(n_comorbidities, len(comorbidities_pool)))
    if not comorbidities:
        comorbidities = ["None"]

    special_cond = random.choices(_SPECIAL_CONDITIONS, weights=_SPECIAL_CONDITION_WEIGHTS)[0]

    patient_seed = {
        "patient_id": f"P-{patient_num:04d}",
        "age": age,
        "sex": sex,
        "ethnicity": ethnicity,
        "weight_kg": round(bmi * random.gauss(1.72, 0.09) ** 2, 1),
        "bmi": bmi,
        "comorbidities": comorbidities,
        "variants": variants,
        "hla_haplotype": hla,
        "apoe_genotype": apoe,
        "vaccination_history": vacc_history,
        "target_vaccine": random.choice(VACCINE_PLATFORMS),
        "special_condition": special_cond.value,
    }

    if CLUSTAN_OMEGA_ENABLED:
        clust_patient = _simulate_patient_with_clustan_omega(patient_seed)
        if clust_patient:
            return clust_patient

    return SyntheticPatient(
        patient_id=patient_seed["patient_id"],
        age=patient_seed["age"],
        sex=patient_seed["sex"],
        ethnicity=patient_seed["ethnicity"],
        weight_kg=patient_seed["weight_kg"],
        bmi=patient_seed["bmi"],
        comorbidities=patient_seed["comorbidities"],
        variants=patient_seed["variants"],
        hla_haplotype=patient_seed["hla_haplotype"],
        apoe_genotype=patient_seed["apoe_genotype"],
        vaccination_history=patient_seed["vaccination_history"],
        target_vaccine=patient_seed["target_vaccine"],
        special_condition=patient_seed["special_condition"],
    )


def generate_cohort(n: int = COHORT_SIZE, seed: int = RANDOM_SEED) -> list[SyntheticPatient]:
    """Generate a synthetic cohort of n patients."""
    random.seed(seed)
    cohort = [generate_patient(i + 1) for i in range(n)]
    logger.info(f"Generated synthetic cohort: {len(cohort)} patients")
    return cohort


def save_cohort(cohort: list[SyntheticPatient], filename: str = "cohort.json"):
    os.makedirs(PATIENTS_DIR, exist_ok=True)
    path = os.path.join(PATIENTS_DIR, filename)
    with open(path, "w") as f:
        json.dump([p.to_dict() for p in cohort], f, indent=2)
    logger.info(f"Saved cohort ({len(cohort)} patients) to {path}")
    return path


def load_cohort(filename: str = "cohort.json") -> list[SyntheticPatient]:
    path = os.path.join(PATIENTS_DIR, filename)
    if not os.path.exists(path):
        return []
    with open(path) as f:
        data = json.load(f)

    valid_patients = []
    for raw in data:
        try:
            patient = SyntheticPatient.from_dict(raw)
            valid_patients.append(patient)
        except Exception as exc:
            logger.warning(f"Skipping invalid patient record in cohort file: {exc}")
    return valid_patients


def get_or_generate_cohort(n: int = COHORT_SIZE) -> list[SyntheticPatient]:
    cohort = load_cohort()
    if len(cohort) >= n:
        return cohort[:n]
    logger.info(f"Generating new cohort of {n} patients...")
    cohort = generate_cohort(n)
    save_cohort(cohort)
    return cohort
