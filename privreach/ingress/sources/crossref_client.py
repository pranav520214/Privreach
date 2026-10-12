"""
CrossRef REST API Harvester Client.

Queries CrossRef's metadata repository (150M+ DOI records)
with official peer-reviewed citations and journal container titles.
"""

from typing import List, Dict, Any, Optional
import urllib.parse
import httpx


class CrossRefClient:
    """Client for CrossRef REST API harvesting."""

    BASE_URL = "https://api.crossref.org/works"

    def __init__(self, mailto: str = "research@privreach.org", timeout: float = 20.0):
        self.timeout = timeout
        self.headers = {
            "User-Agent": f"PrivreachOS-Ingress/3.0 (mailto:{mailto})"
        }

    def search(self, query: str, rows: int = 15) -> List[Dict[str, Any]]:
        """
        Executes a search against the CrossRef works endpoint.
        """
        params = {
            "query": query,
            "rows": min(50, rows),
            "sort": "relevance",
        }
        url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"

        try:
            with httpx.Client(timeout=self.timeout, headers=self.headers, follow_redirects=True) as client:
                resp = client.get(url)
                if resp.status_code != 200:
                    return []
                data = resp.json()
                items = data.get("message", {}).get("items", [])
                return self._parse_items(items)
        except Exception:
            return []

    async def search_async(self, query: str, rows: int = 15) -> List[Dict[str, Any]]:
        """Asynchronous version of CrossRef search."""
        params = {
            "query": query,
            "rows": min(50, rows),
            "sort": "relevance",
        }
        url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers, follow_redirects=True) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return []
                data = resp.json()
                items = data.get("message", {}).get("items", [])
                return self._parse_items(items)
        except Exception:
            return []

    def _parse_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Standardizes CrossRef item objects."""
        records: List[Dict[str, Any]] = []
        for item in items:
            doi = item.get("DOI")
            titles = item.get("title", [])
            title = titles[0] if titles else "Untitled"

            # Venue / Journal container
            containers = item.get("container-title", [])
            venue = containers[0] if containers else ""

            # Citation count
            citations = item.get("is-referenced-by-count", 0)

            # Publication year
            pub_year = 2024
            pub_date = item.get("published-print") or item.get("published-online") or item.get("issued")
            if pub_date and "date-parts" in pub_date and pub_date["date-parts"]:
                parts = pub_date["date-parts"][0]
                if parts and isinstance(parts[0], int):
                    pub_year = parts[0]

            # Authors
            authors: List[str] = []
            for a in item.get("author", []):
                name = f"{a.get('given', '')} {a.get('family', '')}".strip()
                if name:
                    authors.append(name)

            # PDF link if directly available in CrossRef links
            pdf_url = None
            for link in item.get("link", []):
                if link.get("content-type") == "application/pdf":
                    pdf_url = link.get("URL")
                    break

            records.append({
                "paper_id": f"crossref_{doi.replace('/', '_')}" if doi else f"crossref_{hash(title)}",
                "title": title,
                "authors": authors,
                "abstract": "",  # CrossRef rarely supplies full abstracts in standard endpoint
                "doi": doi,
                "venue": venue,
                "publication_year": pub_year,
                "citation_count": citations,
                "pdf_url": pdf_url,
                "source": "crossref",
            })
        return records
