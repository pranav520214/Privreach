"""
OpenAlex REST API Harvester Client.

Queries the global OpenAlex scholarly database (250M+ works)
with citation counts, peer-reviewed venues, and open access PDF locators.
"""

from typing import List, Dict, Any, Optional
import urllib.parse
import httpx


class OpenAlexClient:
    """Client for OpenAlex research paper harvesting."""

    BASE_URL = "https://api.openalex.org/works"

    def __init__(self, mailto: str = "research@privreach.org", timeout: float = 20.0):
        self.timeout = timeout
        self.headers = {
            "User-Agent": f"PrivreachOS-Ingress/3.0 (mailto:{mailto})"
        }

    @staticmethod
    def reconstruct_abstract(inverted_index: Optional[Dict[str, List[int]]]) -> str:
        """
        Reconstructs sequential abstract string from OpenAlex's inverted index format:
        {"word": [pos1, pos2]} -> "word1 word2 ..."
        """
        if not inverted_index:
            return ""
        position_word_map: Dict[int, str] = {}
        for word, positions in inverted_index.items():
            for pos in positions:
                position_word_map[pos] = word

        sorted_positions = sorted(position_word_map.keys())
        return " ".join(position_word_map[pos] for pos in sorted_positions)

    def search(self, query: str, per_page: int = 15) -> List[Dict[str, Any]]:
        """
        Executes a search against OpenAlex works endpoint.
        """
        params = {
            "search": query,
            "per_page": min(50, per_page),
            "sort": "cited_by_count:desc",
        }
        url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"

        try:
            with httpx.Client(timeout=self.timeout, headers=self.headers, follow_redirects=True) as client:
                resp = client.get(url)
                if resp.status_code != 200:
                    return []
                data = resp.json()
                return self._parse_works(data.get("results", []))
        except Exception:
            return []

    async def search_async(self, query: str, per_page: int = 15) -> List[Dict[str, Any]]:
        """Asynchronous version of OpenAlex search."""
        params = {
            "search": query,
            "per_page": min(50, per_page),
            "sort": "cited_by_count:desc",
        }
        url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers, follow_redirects=True) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return []
                data = resp.json()
                return self._parse_works(data.get("results", []))
        except Exception:
            return []

    def _parse_works(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Standardizes OpenAlex work objects."""
        records: List[Dict[str, Any]] = []
        for item in results:
            openalex_id = item.get("id", "").split("/")[-1]
            title = item.get("title") or "Untitled"
            doi = item.get("doi")
            pub_year = item.get("publication_year") or 2024
            citations = item.get("cited_by_count") or 0

            # Reconstruct abstract
            abstract = self.reconstruct_abstract(item.get("abstract_inverted_index"))

            # Primary venue name
            venue = ""
            primary_loc = item.get("primary_location") or {}
            source_info = primary_loc.get("source") or {}
            if source_info and source_info.get("display_name"):
                venue = source_info.get("display_name")

            # Extract authors
            authors: List[str] = []
            for authorship in item.get("authorships", []):
                author_obj = authorship.get("author") or {}
                if author_obj.get("display_name"):
                    authors.append(author_obj.get("display_name"))

            # Open Access PDF locator
            pdf_url = None
            oa_info = item.get("open_access") or {}
            if oa_info.get("oa_url") and oa_info.get("is_oa"):
                pdf_url = oa_info.get("oa_url")
            elif primary_loc.get("pdf_url"):
                pdf_url = primary_loc.get("pdf_url")

            records.append({
                "paper_id": f"openalex_{openalex_id}",
                "title": title,
                "authors": authors,
                "abstract": abstract,
                "doi": doi,
                "venue": venue,
                "publication_year": pub_year,
                "citation_count": citations,
                "pdf_url": pdf_url,
                "source": "openalex",
            })
        return records
