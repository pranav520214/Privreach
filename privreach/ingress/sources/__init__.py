"""Data source clients for academic harvesting."""

from privreach.ingress.sources.arxiv_client import ArxivClient
from privreach.ingress.sources.openalex_client import OpenAlexClient
from privreach.ingress.sources.crossref_client import CrossRefClient

__all__ = ["ArxivClient", "OpenAlexClient", "CrossRefClient"]
