import os
from dotenv import load_dotenv

load_dotenv()

# Azure AI Foundry — Agents API
# AZURE_AI_PROJECT_ENDPOINT: hub endpoint, e.g. https://<hub>.services.ai.azure.com
# AZURE_AI_PROJECT_KEY: API key from ai.azure.com → Settings → Keys and Endpoints
AZURE_AI_PROJECT_ENDPOINT = os.getenv("AZURE_AI_PROJECT_ENDPOINT", "")
AZURE_AI_PROJECT_KEY = os.getenv("AZURE_AI_PROJECT_KEY", "")
AZURE_AI_AGENT_MODEL = os.getenv("AZURE_AI_AGENT_MODEL", "gpt-4o")

# Azure OpenAI (simpler Foundry IQ mode — only needs endpoint + key or az login)
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")

# GitHub Models (Azure AI Inference endpoint — free, no credit card)
# Get token: github.com/settings/tokens → New token → no special scopes needed
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

# OpenRouter (free tier — used as fallback / demo mode when GITHUB_TOKEN is
# missing or expired). Get key: openrouter.ai/keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-super-120b-a12b:free")

# Azure AI Search
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX", "vaccinegenics-knowledge")

# NCBI
NCBI_API_KEY = os.getenv("NCBI_API_KEY", "")
NCBI_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
NCBI_ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

# External simulation engine support
CLUSTAN_OMEGA_ENDPOINT = os.getenv("CLUSTAN_OMEGA_ENDPOINT", "")
CLUSTAN_OMEGA_ENABLED = bool(CLUSTAN_OMEGA_ENDPOINT)

# Simulation
COHORT_SIZE = int(os.getenv("COHORT_SIZE", "1000"))
RANDOM_SEED = 42

# Gene panel (curated per VaccineGenics technical spec)
TARGET_GENES = [
    "TLR4", "TLR7", "TLR9",
    "HLA-A", "HLA-B", "HLA-C", "HLA-DRB1",
    "STAT3", "STAT1",
    "IL6",
    "TMPRSS2",
    "APOE",
    "PEG3",
]

# gnomAD allele frequency cutoff.
# 0.4 is intentionally broad to capture common functional variants (HLA alleles,
# TLR4 coding variants) that have high population frequency but meaningful effect
# size on vaccine immunogenicity. Adjust downward for rare-variant analyses.
MAX_ALLELE_FREQUENCY = 0.4

# Module weights (must sum to 1.0)
# Values informed by the relative emphasis on each pathway in the vaccinomics
# literature. The exact numbers are modeling decisions; the Poland papers below
# justify the ordering (HLA > TLR > STAT > LNP delivery) but do not report
# these specific weights.
#   Poland GA et al. Vaccinomics and a new paradigm for preventive vaccines. OMICS. 2011 (PMID 22241978)
#   Poland GA et al. Vaccinomics, adversomics, and the coming age of individualized vaccines. Ann Rev Med. 2018 (PMID 28774561)
#   Poland GA et al. Immunogenomics in vaccine development. Semin Immunol. 2013 (PMID 23755893)
MODULE_WEIGHTS = {
    "tlr": 0.35,       # Innate pattern recognition — TLR4/7/9 signal amplitude
    "hla": 0.40,       # Adaptive antigen presentation — HLA class I/II allele effect size
    "stat": 0.20,      # Cytokine amplification — IL-6/STAT3 inflammatory burst
    "apoe_peg3": 0.05, # LNP delivery — APOE-mediated nanoparticle clearance
}


def validate_module_weights(weights: dict) -> None:
    total = sum(weights.values())
    if abs(total - 1.0) > 1e-6:
        raise ValueError(
            f"MODULE_WEIGHTS must sum to 1.0, but sum is {total:.6f}. "
            "Adjust config.py to maintain normalized module weights."
        )

validate_module_weights(MODULE_WEIGHTS)

# Vaccine platform IRT parameters (b = difficulty threshold)
VACCINE_IRT_PARAMS = {
    "mRNA": {"b": -0.5, "a": 1.5, "c": 0.05},          # High reactogenicity → low difficulty
    "adenoviral_vector": {"b": 0.0, "a": 1.2, "c": 0.05},
    "protein_subunit": {"b": 0.8, "a": 1.0, "c": 0.05}, # Requires strong genetic responder
}

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
VARIANTS_DIR = os.path.join(DATA_DIR, "variants")
PATIENTS_DIR = os.path.join(DATA_DIR, "patients")
KNOWLEDGE_BASE_DIR = os.path.join(DATA_DIR, "knowledge_base")

# Validate platform definitions so code can rely on exact keys.
REQUIRED_VACCINE_PLATFORMS = {"mRNA", "adenoviral_vector", "protein_subunit"}
if set(VACCINE_IRT_PARAMS.keys()) != REQUIRED_VACCINE_PLATFORMS:
    raise ValueError(
        f"VACCINE_IRT_PARAMS must define exactly {REQUIRED_VACCINE_PLATFORMS}. "
        f"Found: {set(VACCINE_IRT_PARAMS.keys())}"
    )
