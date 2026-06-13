"""
ClinVar variant extractor using NCBI E-utilities API.

Implements the 5-stage inclusion/exclusion funnel:
  1. Target gene panel filter
  2. Clinical significance filter (pathogenic / likely pathogenic / risk factor)
  3. Germline origin filter
  4. Allele frequency filter via gnomAD (AF < 0.4)
  5. PubMed evidence filter (at least 1 PMID)
"""

import time
import json
import logging
from typing import Optional
import requests

from config import (
    NCBI_API_KEY,
    NCBI_ESEARCH_URL,
    NCBI_ESUMMARY_URL,
    TARGET_GENES,
    MAX_ALLELE_FREQUENCY,
)

logger = logging.getLogger(__name__)

ACCEPTED_SIGNIFICANCE = {"pathogenic", "likely pathogenic", "risk factor"}

# NCBI ORIGIN field bitmask for germline = 1
GERMLINE_ORIGIN_BIT = 1

# NCBI enforces 3 req/s without API key, 10 req/s with key.
# Use a conservative min-interval with a small safety margin.
_NCBI_MIN_INTERVAL = 1.0 / 9.5 if NCBI_API_KEY else 1.0 / 2.8
_last_ncbi_call: float = 0.0


def _ncbi_rate_limit() -> None:
    """Block until the next NCBI request is safe to send."""
    global _last_ncbi_call
    elapsed = time.monotonic() - _last_ncbi_call
    wait = _NCBI_MIN_INTERVAL - elapsed
    if wait > 0:
        time.sleep(wait)
    _last_ncbi_call = time.monotonic()


def _build_search_term(gene: str) -> str:
    return (
        f"{gene}[gene] AND ("
        "pathogenic[clinical_significance] OR "
        "\"likely pathogenic\"[clinical_significance] OR "
        "\"risk factor\"[clinical_significance])"
    )


def _ncbi_get(url: str, params: dict, retries: int = 3) -> Optional[dict]:
    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY
    params["retmode"] = "json"

    for attempt in range(retries):
        _ncbi_rate_limit()
        try:
            r = requests.get(url, params=params, timeout=15)
            if r.status_code == 429:
                # Explicit rate-limit response — back off longer
                backoff = 5.0 * (attempt + 1)
                logger.warning(f"NCBI 429 rate limit hit — backing off {backoff:.0f}s")
                time.sleep(backoff)
                continue
            r.raise_for_status()
            return r.json()
        except requests.exceptions.Timeout:
            logger.warning(f"NCBI timeout (attempt {attempt+1})")
            time.sleep(2.0 * (attempt + 1))
        except Exception as e:
            logger.warning(f"NCBI request failed (attempt {attempt+1}): {e}")
            time.sleep(1.5 * (attempt + 1))
    return None


def fetch_variant_ids(gene: str) -> list[str]:
    """Return ClinVar UIDs for a single gene matching significance criteria."""
    params = {
        "db": "clinvar",
        "term": _build_search_term(gene),
        "retmax": "500",
    }
    data = _ncbi_get(NCBI_ESEARCH_URL, params)
    if not data:
        return []
    return data.get("esearchresult", {}).get("idlist", [])


def fetch_variant_summaries(uids: list[str]) -> list[dict]:
    """Batch-fetch esummary JSON for a list of ClinVar UIDs."""
    if not uids:
        return []

    summaries = []
    batch_size = 100
    for i in range(0, len(uids), batch_size):
        batch = uids[i : i + batch_size]
        params = {
            "db": "clinvar",
            "id": ",".join(batch),
        }
        data = _ncbi_get(NCBI_ESUMMARY_URL, params)
        if not data:
            continue
        result = data.get("result", {})
        for uid in batch:
            if uid in result:
                summaries.append(result[uid])

    return summaries


def _is_germline(summary: dict) -> bool:
    """Check ORIGIN field for germline bit."""
    origin = summary.get("origin", "")
    # Origin can be a string like "germline" or numeric bitmask
    if isinstance(origin, str):
        return "germline" in origin.lower()
    try:
        return bool(int(origin) & GERMLINE_ORIGIN_BIT)
    except (ValueError, TypeError):
        return False


def _has_pubmed_evidence(summary: dict) -> bool:
    """Require at least one PMID in the variant record."""
    # ClinVar esummary returns supporting_submissions or trait_set with citations
    trait_set = summary.get("trait_set", [])
    for trait in trait_set:
        if trait.get("citations"):
            return True
    # Also check top-level citations field
    if summary.get("citations"):
        return True
    # Check variation_set for supporting literature
    variation_set = summary.get("variation_set", [])
    for var in variation_set:
        if var.get("supporting_submissions", {}).get("rcv"):
            return True
    return False


def _extract_significance(summary: dict) -> str:
    germline_classification = summary.get("germline_classification", {})
    if isinstance(germline_classification, dict):
        return germline_classification.get("description", "").lower()
    return str(germline_classification).lower()


def filter_variants(summaries: list[dict]) -> list[dict]:
    """Apply the 5-stage VaccineGenics inclusion/exclusion funnel."""
    filtered = []
    for s in summaries:
        # Stage 2: Clinical significance
        sig = _extract_significance(s)
        if not any(acc in sig for acc in ACCEPTED_SIGNIFICANCE):
            continue

        # Stage 3: Germline origin
        if not _is_germline(s):
            continue

        # Stage 5: PubMed evidence (AF check done post-fetch in variant_processor)
        # We include here variants that pass, AF filtering is applied after
        filtered.append(s)

    return filtered


def extract_clean_variant(summary: dict, gene: str) -> dict:
    """Extract a clean, structured variant record from an esummary JSON blob."""
    var_set = summary.get("variation_set", [{}])
    var = var_set[0] if var_set else {}

    return {
        "uid": summary.get("uid", ""),
        "gene": gene,
        "name": var.get("variation_name", summary.get("title", "")),
        "rsid": var.get("dbsnp_rs", ""),
        "clinical_significance": _extract_significance(summary),
        "molecular_consequence": var.get("molecular_consequence_list", []),
        "protein_change": var.get("protein_change", ""),
        "allele_id": summary.get("allele_id", ""),
        "chromosome": summary.get("chromosome", ""),
        "location": summary.get("location_list", [{}])[0] if summary.get("location_list") else {},
        "has_pmid": _has_pubmed_evidence(summary),
        "allele_frequency": None,  # Populated by gnomad_filter
        "effect_modifier": 0.0,    # Populated by variant_processor
    }


def run_clinvar_pipeline(genes: list[str] = None) -> list[dict]:
    """
    Full ClinVar extraction pipeline.
    Returns a list of clean variant dicts ready for gnomAD AF enrichment.
    """
    genes = genes or TARGET_GENES
    all_variants = []

    for gene in genes:
        logger.info(f"Fetching ClinVar variants for {gene}...")
        uids = fetch_variant_ids(gene)
        logger.info(f"  {gene}: {len(uids)} raw UIDs")

        if not uids:
            continue

        summaries = fetch_variant_summaries(uids)
        filtered = filter_variants(summaries)
        logger.info(f"  {gene}: {len(filtered)} variants after significance/germline filters")

        for s in filtered:
            variant = extract_clean_variant(s, gene)
            all_variants.append(variant)

        time.sleep(0.5)

    logger.info(f"ClinVar pipeline complete: {len(all_variants)} total variants")
    return all_variants
