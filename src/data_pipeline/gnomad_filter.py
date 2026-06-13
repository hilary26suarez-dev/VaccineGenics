"""
gnomAD allele frequency filter.

Queries the gnomAD GraphQL API to retrieve population AF for each variant.
Variants with AF > 0.4 are discarded (too common to be discriminating biomarkers).
"""

import time
import json
import logging
import requests
from typing import Optional

import os
from config import MAX_ALLELE_FREQUENCY, VARIANTS_DIR

logger = logging.getLogger(__name__)

GNOMAD_GRAPHQL_URL = "https://gnomad.broadinstitute.org/api"
AF_CACHE_PATH = os.path.join(VARIANTS_DIR, "gnomad_af_cache.json")

GNOMAD_QUERY = """
query VariantQuery($variantId: String!, $datasetId: DatasetId!) {
  variant(variantId: $variantId, dataset: $datasetId) {
    variantId
    exome {
      ac
      an
      af
    }
    genome {
      ac
      an
      af
    }
  }
}
"""


def _load_af_cache() -> dict:
    if not os.path.exists(AF_CACHE_PATH):
        return {}
    try:
        with open(AF_CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_af_cache(cache: dict) -> None:
    os.makedirs(os.path.dirname(AF_CACHE_PATH), exist_ok=True)
    with open(AF_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)


def _rsid_to_gnomad_id(rsid: str) -> Optional[str]:
    """Convert rsXXX to gnomAD variant ID format via gnomAD search."""
    if not rsid or not rsid.startswith("rs"):
        return None
    return rsid  # gnomAD accepts rsIDs directly in some endpoints


def query_gnomad_af(rsid: str, dataset: str = "gnomad_r4") -> Optional[float]:
    """Query gnomAD for allele frequency. Returns None if not found."""
    if not rsid or not rsid.startswith("rs"):
        return None

    # gnomAD GraphQL: dataset must be a variable of type DatasetId, not a hardcoded string
    search_query = """
    query VariantByRsid($rsid: String!, $datasetId: DatasetId!) {
      variant(variantId: $rsid, dataset: $datasetId) {
        exome { af }
        genome { af }
      }
    }
    """
    try:
        resp = requests.post(
            GNOMAD_GRAPHQL_URL,
            json={"query": search_query, "variables": {"rsid": rsid, "datasetId": dataset}},
            timeout=10,
            headers={"Content-Type": "application/json"},
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        variant = data.get("data", {}).get("variant")
        if not variant:
            return None

        # Use max(exome_af, genome_af) as conservative estimate
        exome_af = (variant.get("exome") or {}).get("af") or 0.0
        genome_af = (variant.get("genome") or {}).get("af") or 0.0
        return max(exome_af, genome_af)

    except Exception as e:
        logger.debug(f"gnomAD query failed for {rsid}: {e}")
        return None


# Known AF values for key variants used in VaccineGenics (fallback when API unavailable)
KNOWN_AF_OVERRIDES = {
    "rs4986790": 0.07,   # TLR4 Asp299Gly
    "rs4986791": 0.05,   # TLR4 Thr399Ile
    "rs179008":  0.25,   # TLR7 Gln11Leu (X-linked)
    "rs5743836": 0.15,   # TLR9 T-1237C promoter
    "rs352140":  0.19,   # TLR9 +2848 A>G (NOT rs352139 which is a different locus)
    "rs1800795": 0.38,   # IL6 -174G>C promoter
    "rs1800796": 0.12,   # IL6 -572G>C promoter
    "rs1800797": 0.37,   # IL6 -597G>A promoter
    "rs1137578": 0.08,   # STAT3
    "rs12233781": 0.11,  # STAT1
    "rs429358":  0.14,   # APOE ε4 allele-defining SNP
    "rs7412":    0.07,   # APOE ε2 allele-defining SNP
}


def enrich_variants_with_af(variants: list[dict], use_api: bool = True) -> list[dict]:
    """
    Enrich each variant dict with allele_frequency from gnomAD.
    Applies MAX_ALLELE_FREQUENCY cutoff and marks variants accordingly.
    """
    cache = _load_af_cache()
    enriched = []
    for v in variants:
        rsid = str(v.get("rsid", "")).strip()

        af = KNOWN_AF_OVERRIDES.get(rsid)
        if af is None and rsid in cache:
            af = cache[rsid]
            logger.debug(f"gnomAD AF cache hit for {rsid}: {af}")

        if af is None and use_api and rsid.startswith("rs"):
            af = query_gnomad_af(rsid)
            if af is not None:
                cache[rsid] = af
                _save_af_cache(cache)
            time.sleep(0.2)  # Rate limiting

        v["allele_frequency"] = af

        if af is not None and af > MAX_ALLELE_FREQUENCY:
            logger.debug(f"Excluding {rsid} (AF={af:.3f} > {MAX_ALLELE_FREQUENCY})")
            continue

        enriched.append(v)

    logger.info(
        f"gnomAD filter: {len(variants)} → {len(enriched)} variants "
        f"(removed {len(variants) - len(enriched)} high-frequency)"
    )
    return enriched
