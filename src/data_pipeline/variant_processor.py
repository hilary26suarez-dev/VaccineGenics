"""
Variant processor: combines ClinVar + gnomAD results into the final
curated variant panel used by the pharmacogenomics simulation engine.

Also assigns the effect_modifier score (-1.0 to +1.0) for each variant.
"""

import json
import logging
import os
from pathlib import Path

from .clinvar_extractor import run_clinvar_pipeline
from .gnomad_filter import enrich_variants_with_af

from config import VARIANTS_DIR, TARGET_GENES

logger = logging.getLogger(__name__)

# Effect modifier lookup: rsID → effect_modifier
# Negative = loss-of-function / hypo-immune; Positive = gain-of-function / hyper-immune
EFFECT_MODIFIERS = {
    # TLR pathway
    "rs4986790": -0.35,  # TLR4 Asp299Gly — loss of function, reduced NF-κB
    "rs4986791": -0.30,  # TLR4 Thr399Ile — impaired signaling
    "rs179008":  -0.25,  # TLR7 Gln11Leu — reduced innate sensing
    "rs5743836": +0.20,  # TLR9 T-1237C — increased promoter activity

    # HLA variants — efficacy
    "HLA-A*02:01":    +0.40,  # Strong CD8+ T-cell response
    "HLA-B*40:01":    +0.30,  # High NAb titers
    "HLA-DRB1*03:01": +0.35,  # Robust CD4+ helper response
    "HLA-DQB1*06:02": +0.25,  # Enhanced memory formation

    # HLA variants — toxicity risk (autoinflammatory)
    "HLA-DRB1*11:04": -0.50,  # VITT risk (thrombocytopenia with adenoviral)
    "HLA-B*35:01":    -0.30,  # Suboptimal response
    "HLA-C*07:01":    -0.25,  # Reduced protection
    "HLA-DRB1*01:01": -0.20,  # Lower NAb titers
    "HLA-B*35":       -0.35,  # Thyroiditis risk
    "HLA-C*04":       -0.30,  # Post-vaccine autoimmune thyroiditis

    # Cytokine / STAT pathway
    "rs1800795": +0.30,  # IL6 -174G>C — GG homozygous = higher IgG titers
    "rs1800796": +0.15,  # IL6 promoter moderate effect
    "rs1800797": +0.20,  # IL6 promoter moderate effect
    "rs1137578": -0.20,  # STAT3 LOF variant
    "rs12233781": +0.15, # STAT1 gain-of-function

    # APOE / lipid bioavailability
    "rs429358": -0.40,   # APOE ε4 — prolonged LNP retention, mitochondrial stress
    "rs7412":   +0.10,   # APOE ε2 — slightly favorable LNP clearance
}

# Module assignment per gene
GENE_MODULE_MAP = {
    "TLR4":    "tlr",
    "TLR7":    "tlr",
    "TLR9":    "tlr",
    "HLA-A":   "hla",
    "HLA-B":   "hla",
    "HLA-C":   "hla",
    "HLA-DRB1":"hla",
    "STAT3":   "stat",
    "STAT1":   "stat",
    "IL6":     "stat",
    "TMPRSS2": "stat",
    "APOE":    "apoe_peg3",
    "PEG3":    "apoe_peg3",
}


def assign_effect_modifiers(variants: list[dict]) -> list[dict]:
    for v in variants:
        rsid = str(v.get("rsid", "")).strip()
        name = str(v.get("name", "")).strip()

        # Try rsID match first
        modifier = EFFECT_MODIFIERS.get(rsid)

        # Try HLA allele name match
        if modifier is None:
            for key, val in EFFECT_MODIFIERS.items():
                if key in name:
                    modifier = val
                    break

        # Default by clinical significance if no specific modifier
        if modifier is None:
            sig = v.get("clinical_significance", "")
            if "pathogenic" in sig:
                modifier = -0.20  # Conservative negative for unknown pathogenic
            elif "risk factor" in sig:
                modifier = -0.10
            else:
                modifier = 0.0

        v["effect_modifier"] = modifier
        v["module"] = GENE_MODULE_MAP.get(v.get("gene", ""), "unknown")

    return variants


def save_variant_panel(variants: list[dict], filename: str = "variant_panel.json"):
    os.makedirs(VARIANTS_DIR, exist_ok=True)
    path = os.path.join(VARIANTS_DIR, filename)
    with open(path, "w") as f:
        json.dump(variants, f, indent=2)
    logger.info(f"Saved {len(variants)} variants to {path}")
    return path


def load_variant_panel(filename: str = "variant_panel.json") -> list[dict]:
    path = os.path.join(VARIANTS_DIR, filename)
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)


def build_variant_panel(
    genes: list[str] = None,
    use_cached: bool = True,
    use_gnomad_api: bool = True,
) -> list[dict]:
    """
    Full pipeline: ClinVar → gnomAD filter → effect modifier assignment.
    Returns the curated variant panel.
    """
    cache_path = os.path.join(VARIANTS_DIR, "variant_panel.json")

    if use_cached and os.path.exists(cache_path):
        logger.info("Loading cached variant panel...")
        variants = load_variant_panel()
        logger.info(f"Loaded {len(variants)} variants from cache")
        return variants

    logger.info("Building variant panel from scratch...")
    variants = run_clinvar_pipeline(genes or TARGET_GENES)
    variants = enrich_variants_with_af(variants, use_api=use_gnomad_api)
    variants = assign_effect_modifiers(variants)
    save_variant_panel(variants)

    logger.info(f"Variant panel built: {len(variants)} curated variants")
    return variants


def get_module_variants(variants: list[dict], module: str) -> list[dict]:
    return [v for v in variants if v.get("module") == module]
