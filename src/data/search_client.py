"""
Azure AI Search grounding for VaccineGenics.

This is the real Foundry IQ knowledge-retrieval layer.

Setup (one-time):
  1. Create a free Azure AI Search resource (F1 tier):
       portal.azure.com → Create resource → Azure AI Search → Free (F1)
  2. Add to .env:
       AZURE_SEARCH_ENDPOINT=https://<service-name>.search.windows.net
       AZURE_SEARCH_KEY=<admin-key>
  3. Run once:
       python setup_search.py

Dra. Evidencia then queries Azure AI Search for every patient.
Falls back to the local literature_kb.py dict automatically if Azure is not configured.

Install: pip install azure-search-documents>=11.4.0  (included in pip install -e ".[azure]")
"""

from __future__ import annotations

import hashlib
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


# ── Configuration helpers (read lazily so .env is always loaded first) ────────

def _endpoint() -> str:
    return os.getenv("AZURE_SEARCH_ENDPOINT", "")


def _key() -> str:
    return os.getenv("AZURE_SEARCH_KEY", "")


def _index_name() -> str:
    return os.getenv("AZURE_SEARCH_INDEX", "vaccinegenics-knowledge")


# ── Availability check (cached per process) ───────────────────────────────────

_available: Optional[bool] = None
_search_client = None


def is_available() -> bool:
    """
    Return True if Azure AI Search is configured and the index is reachable.
    Result is cached for the lifetime of the process.
    """
    global _available
    if _available is not None:
        return _available

    if not _endpoint() or not _key():
        _available = False
        return False

    try:
        from azure.search.documents import SearchClient
        from azure.core.credentials import AzureKeyCredential
    except ImportError:
        _available = False
        logger.debug("azure-search-documents not installed — using local KB")
        return False

    try:
        client = SearchClient(
            endpoint=_endpoint(),
            index_name=_index_name(),
            credential=AzureKeyCredential(_key()),
        )
        client.get_document_count()
        _available = True
        logger.info("Azure AI Search: index '%s' ready", _index_name())
    except Exception as exc:
        _available = False
        logger.warning("Azure AI Search unavailable (%s) — using local KB", exc)

    return _available


# ── Search ────────────────────────────────────────────────────────────────────

def _get_search_client():
    global _search_client
    if _search_client is None:
        from azure.search.documents import SearchClient
        from azure.core.credentials import AzureKeyCredential
        _search_client = SearchClient(
            endpoint=_endpoint(),
            index_name=_index_name(),
            credential=AzureKeyCredential(_key()),
        )
    return _search_client


def search_citations(
    query: str,
    top: int = 5,
    category_filter: str = None,
) -> list[dict]:
    """
    Full-text search against the Azure AI Search knowledge index.

    Returns citation dicts matching literature_kb.py format:
      {pmid, authors, year, journal, title, relevance, excerpt, category}
    """
    if not is_available():
        return []

    try:
        client = _get_search_client()
        filter_expr = f"category eq '{category_filter}'" if category_filter else None
        results = client.search(
            search_text=query,
            top=top,
            filter=filter_expr,
            select=[
                "doc_id", "category", "pmid", "authors", "year_pub",
                "journal", "title", "relevance", "excerpt",
            ],
            query_type="simple",
        )
        citations: list[dict] = []
        seen_pmids: set[str] = set()
        for r in results:
            pmid = r.get("pmid", "")
            if not pmid or pmid in seen_pmids:
                continue
            seen_pmids.add(pmid)
            citations.append({
                "category": r.get("category", ""),
                "pmid": pmid,
                "authors": r.get("authors", ""),
                "year": r.get("year_pub", 0),
                "journal": r.get("journal", ""),
                "title": r.get("title", ""),
                "relevance": r.get("relevance", ""),
                "excerpt": r.get("excerpt", ""),
            })
        logger.info(
            "Azure AI Search: query='%s' → %d results", query[:60], len(citations)
        )
        return citations
    except Exception as exc:
        logger.error("Azure AI Search query failed: %s", exc)
        return []


# ── Index management (called from setup_search.py only) ──────────────────────

def _build_index_schema():
    from azure.search.documents.indexes.models import (
        SearchIndex,
        SimpleField,
        SearchableField,
        SearchFieldDataType,
    )
    fields = [
        SimpleField(name="doc_id",    type=SearchFieldDataType.String, key=True),
        SimpleField(name="category",  type=SearchFieldDataType.String,
                    filterable=True, facetable=True),
        SimpleField(name="pmid",      type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="year_pub",  type=SearchFieldDataType.Int32,
                    filterable=True, sortable=True),
        SearchableField(name="authors",     type=SearchFieldDataType.String),
        SearchableField(name="journal",     type=SearchFieldDataType.String),
        SearchableField(name="title",       type=SearchFieldDataType.String),
        SearchableField(name="relevance",   type=SearchFieldDataType.String,
                        analyzer_name="es.lucene"),
        SearchableField(name="excerpt",     type=SearchFieldDataType.String,
                        analyzer_name="es.lucene"),
        # Combined field for higher recall on rsIDs, HLA alleles, condition names
        SearchableField(name="search_body", type=SearchFieldDataType.String),
    ]
    return SearchIndex(name=_index_name(), fields=fields)


def create_index() -> bool:
    """Create the Azure AI Search index. No-op if it already exists."""
    try:
        from azure.search.documents.indexes import SearchIndexClient
        from azure.core.credentials import AzureKeyCredential
    except ImportError:
        logger.error("azure-search-documents not installed")
        return False

    try:
        client = SearchIndexClient(
            endpoint=_endpoint(),
            credential=AzureKeyCredential(_key()),
        )
        existing_names = [i.name for i in client.list_indexes()]
        if _index_name() in existing_names:
            logger.info("Index '%s' already exists — skipping creation", _index_name())
            return True
        client.create_index(_build_index_schema())
        logger.info("Index '%s' created successfully", _index_name())
        return True
    except Exception as exc:
        logger.error("Index creation failed: %s", exc)
        return False


def upload_knowledge_base() -> int:
    """
    Upload all literature_kb._LITERATURE entries to Azure AI Search.
    Returns number of documents successfully uploaded.
    """
    # SDK check — separate from _LITERATURE import so errors are clear
    try:
        from azure.search.documents import SearchClient
        from azure.core.credentials import AzureKeyCredential
    except ImportError:
        logger.error(
            "azure-search-documents not installed. "
            "Run: pip install azure-search-documents>=11.4.0"
        )
        return 0

    # Import the raw literature dict (no circular import — this is a function body)
    _LITERATURE = None
    for module_path in ("data.literature_kb", "src.data.literature_kb"):
        try:
            import importlib
            mod = importlib.import_module(module_path)
            _LITERATURE = mod._LITERATURE
            break
        except (ImportError, AttributeError):
            continue

    if _LITERATURE is None:
        logger.error("Cannot import _LITERATURE — run setup_search.py from project root")
        return 0

    # Build documents
    documents: list[dict] = []
    for category, citations in _LITERATURE.items():
        for i, cit in enumerate(citations):
            doc_id = hashlib.md5(f"{category}_{cit.pmid}_{i}".encode()).hexdigest()
            search_body = " ".join([
                category, cit.pmid, cit.authors,
                cit.title, cit.relevance, cit.excerpt,
            ])
            documents.append({
                "doc_id":      doc_id,
                "category":    category,
                "pmid":        cit.pmid,
                "authors":     cit.authors,
                "year_pub":    cit.year,
                "journal":     cit.journal,
                "title":       cit.title,
                "relevance":   cit.relevance,
                "excerpt":     cit.excerpt,
                "search_body": search_body,
            })

    if not documents:
        logger.warning("No documents found in _LITERATURE")
        return 0

    client = SearchClient(
        endpoint=_endpoint(),
        index_name=_index_name(),
        credential=AzureKeyCredential(_key()),
    )

    total = 0
    batch_size = 100
    for start in range(0, len(documents), batch_size):
        batch = documents[start : start + batch_size]
        results = client.upload_documents(documents=batch)
        succeeded = sum(1 for r in results if r.succeeded)
        total += succeeded
        logger.info(
            "Batch %d–%d: %d/%d uploaded",
            start, start + len(batch), succeeded, len(batch),
        )

    logger.info("Knowledge base upload complete: %d documents", total)
    return total
