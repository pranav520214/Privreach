"""
arXiv API Harvester Client.

Performs deterministic query execution against export.arxiv.org,
parsing Atom XML feeds and extracting verified metadata.
"""

from typing import List, Dict, Any, Optional
import urllib.parse
import xml.etree.ElementTree as ET
import hashlib
import os
import httpx
from datetime import datetime


ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


class ArxivClient:
    """Deterministic client for arXiv API harvesting."""

    BASE_URL = "https://export.arxiv.org/api/query"

    def __init__(self, timeout: float = 20.0, user_agent: str = "PrivreachOS-Ingress/3.0"):
        self.timeout = timeout
        self.headers = {"User-Agent": user_agent}

    def search(self, query: str, max_results: int = 15, sort_by: str = "relevance") -> List[Dict[str, Any]]:
        """
        Executes a search against the arXiv API.

        Args:
            query: Free text or search terms (e.g. "all:lithography")
            max_results: Max records to return
            sort_by: "relevance" or "lastUpdatedDate" or "submittedDate"

        Returns:
            List of standardized paper dictionaries.
        """
        # Format query for arXiv API syntax
        encoded_query = urllib.parse.quote(f"all:{query}")
        url = f"{self.BASE_URL}?search_query={encoded_query}&start=0&max_results={max_results}&sortBy={sort_by}"

        try:
            with httpx.Client(timeout=self.timeout, headers=self.headers, follow_redirects=True) as client:
                resp = client.get(url)
                if resp.status_code != 200:
                    return []
                return self.parse_atom_xml(resp.text)
        except Exception:
            return []

    async def search_async(self, query: str, max_results: int = 15, sort_by: str = "relevance") -> List[Dict[str, Any]]:
        """Asynchronous version of search."""
        encoded_query = urllib.parse.quote(f"all:{query}")
        url = f"{self.BASE_URL}?search_query={encoded_query}&start=0&max_results={max_results}&sortBy={sort_by}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers, follow_redirects=True) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return []
                return self.parse_atom_xml(resp.text)
        except Exception:
            return []

    def parse_atom_xml(self, xml_content: str) -> List[Dict[str, Any]]:
        """Parses arXiv Atom XML string into structured records."""
        records: List[Dict[str, Any]] = []
        try:
            root = ET.fromstring(xml_content)
        except Exception:
            return []

        entries = root.findall("atom:entry", ATOM_NS)
        for entry in entries:
            # Check if this is a valid paper entry (ignore error entries)
            id_elem = entry.find("atom:id", ATOM_NS)
            if id_elem is None or not id_elem.text:
                continue
            arxiv_raw_id = id_elem.text.strip()
            # Clean arXiv id (e.g., http://arxiv.org/abs/2103.12345v1 -> 2103.12345)
            arxiv_id = arxiv_raw_id.split("/abs/")[-1].split("v")[0]

            title_elem = entry.find("atom:title", ATOM_NS)
            title = " ".join((title_elem.text or "").split()) if title_elem is not None else "Untitled"

            summary_elem = entry.find("atom:summary", ATOM_NS)
            abstract = " ".join((summary_elem.text or "").split()) if summary_elem is not None else ""

            published_elem = entry.find("atom:published", ATOM_NS)
            pub_year = datetime.now().year
            if published_elem is not None and published_elem.text:
                try:
                    pub_year = int(published_elem.text[:4])
                except Exception:
                    pass

            authors: List[str] = []
            for author_node in entry.findall("atom:author", ATOM_NS):
                name_elem = author_node.find("atom:name", ATOM_NS)
                if name_elem is not None and name_elem.text:
                    authors.append(name_elem.text.strip())

            # Find PDF link
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            for link_elem in entry.findall("atom:link", ATOM_NS):
                if link_elem.attrib.get("title") == "pdf" or link_elem.attrib.get("type") == "application/pdf":
                    pdf_url = link_elem.attrib.get("href", pdf_url)
                    break

            doi_elem = entry.find("arxiv:doi", ATOM_NS)
            doi = doi_elem.text.strip() if doi_elem is not None and doi_elem.text else None

            records.append({
                "paper_id": f"arxiv_{arxiv_id}",
                "title": title,
                "authors": authors,
                "abstract": abstract,
                "doi": doi,
                "venue": "arXiv",
                "publication_year": pub_year,
                "citation_count": 0,  # arXiv feed does not supply citation counts directly
                "pdf_url": pdf_url,
                "source": "arxiv",
            })
        return records

    def download_pdf(self, pdf_url: str, dest_path: str) -> Optional[str]:
        """
        Downloads a PDF file and returns its SHA-256 hash.
        """
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        try:
            with httpx.Client(timeout=60.0, headers=self.headers, follow_redirects=True) as client:
                with client.stream("GET", pdf_url) as resp:
                    if resp.status_code != 200:
                        return None
                    hasher = hashlib.sha256()
                    with open(dest_path, "wb") as f:
                        for chunk in resp.iter_bytes(chunk_size=16384):
                            hasher.update(chunk)
                            f.write(chunk)
                    return hasher.hexdigest()
        except Exception:
            return None
