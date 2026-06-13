#!/usr/bin/env python3
"""
VaccineGenics — Azure AI Search index setup.

Run this once after creating your Azure AI Search resource to:
  1. Create the 'vaccinegenics-knowledge' index
  2. Upload all literature knowledge base documents

Usage:
  python setup_search.py

Prerequisites:
  1. Create a FREE Azure AI Search resource (F1 tier):
       portal.azure.com → Create resource → "Azure AI Search" → Pricing tier: Free (F1)
       Free tier: 50 MB storage, 3 indexes, no credit card needed beyond free Azure credits.

  2. Add to your .env:
       AZURE_SEARCH_ENDPOINT=https://<your-service-name>.search.windows.net
       AZURE_SEARCH_KEY=<your-admin-key>  # From: portal → your resource → Settings → Keys

  3. Install the SDK (included in pip install -e ".[azure]"):
       pip install azure-search-documents>=11.4.0
"""

import sys
import os
import logging

logging.basicConfig(level=logging.INFO, format="[%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("setup_search")

# Make src importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from dotenv import load_dotenv
load_dotenv()


def main():
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT", "")
    key = os.getenv("AZURE_SEARCH_KEY", "")

    if not endpoint or not key:
        logger.error(
            "\n❌  Missing credentials.\n"
            "   Add to your .env:\n"
            "     AZURE_SEARCH_ENDPOINT=https://<service>.search.windows.net\n"
            "     AZURE_SEARCH_KEY=<admin-key>\n\n"
            "   Get them from: portal.azure.com → your AI Search resource → Settings → Keys\n"
        )
        sys.exit(1)

    logger.info("=" * 65)
    logger.info("VaccineGenics — Azure AI Search Setup")
    logger.info("=" * 65)
    logger.info("Endpoint : %s", endpoint)
    logger.info("Index    : %s", os.getenv("AZURE_SEARCH_INDEX", "vaccinegenics-knowledge"))

    try:
        from azure.search.documents.indexes import SearchIndexClient
        from azure.core.credentials import AzureKeyCredential
    except ImportError:
        logger.error(
            "\n❌  azure-search-documents not installed.\n"
            "   Run: pip install azure-search-documents>=11.4.0\n"
            "   Or:  pip install -e '.[azure]'\n"
        )
        sys.exit(1)

    from data.search_client import create_index, upload_knowledge_base

    # Step 1: Create index
    logger.info("\n[1/2] Creating index...")
    if not create_index():
        logger.error("❌  Index creation failed. Check your endpoint/key and try again.")
        sys.exit(1)
    logger.info("✅  Index ready")

    # Step 2: Upload documents
    logger.info("\n[2/2] Uploading knowledge base documents...")
    n = upload_knowledge_base()
    if n == 0:
        logger.error("❌  No documents uploaded. Check logs above.")
        sys.exit(1)
    logger.info("✅  %d documents uploaded to Azure AI Search", n)

    logger.info("\n" + "=" * 65)
    logger.info("✅  Setup complete!")
    logger.info(
        "   Dra. Evidencia will now query Azure AI Search for every patient.\n"
        "   Verify at: portal.azure.com → your AI Search resource → Search explorer"
    )
    logger.info("=" * 65)


if __name__ == "__main__":
    main()
