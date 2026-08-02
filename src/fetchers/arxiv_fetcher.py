import logging
import urllib.request
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class ArxivFetcher:
    def __init__(self, categories: Optional[List[str]] = None):
        if categories is None:
            self.categories = ["cs.AI", "cs.CL", "cs.CV", "cs.LG"]
        else:
            self.categories = categories

    def fetch_latest_papers(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch recent papers from ArXiv API for specified categories.
        First attempts using `arxiv` package if available, else falls back to ArXiv API XML request.
        """
        try:
            import arxiv
            cat_query = " OR ".join([f"cat:{c}" for c in self.categories])
            search = arxiv.Search(
                query=cat_query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            client = arxiv.Client(
                page_size=max_results,
                delay_seconds=3.0,
                num_retries=3
            )
            results = []
            for result in client.results(search):
                # Clean arxiv_id (remove version suffix e.g., '2401.12345v1' -> '2401.12345')
                arxiv_id = result.entry_id.split('/')[-1]
                if 'v' in arxiv_id:
                    arxiv_id = arxiv_id.split('v')[0]
                
                authors = ", ".join([a.name for a in result.authors[:5]])
                if len(result.authors) > 5:
                    authors += " et al."

                results.append({
                    "arxiv_id": arxiv_id,
                    "title": result.title.replace("\n", " ").strip(),
                    "authors": authors,
                    "published": result.published.strftime("%Y-%m-%d") if result.published else "",
                    "summary": result.summary.replace("\n", " ").strip(),
                    "url": f"https://arxiv.org/abs/{arxiv_id}",
                    "categories": result.categories
                })
            logger.info(f"Successfully fetched {len(results)} latest papers via arxiv SDK.")
            return results

        except Exception as e:
            logger.warning(f"arxiv SDK fetch failed or not installed ({e}), waiting 3s before falling back to requests / Atom API...")
            import time
            time.sleep(3)
            return self._fetch_via_requests_or_atom(max_results)

    def _fetch_via_requests_or_atom(self, max_results: int = 10) -> List[Dict[str, Any]]:
        cat_query = "+OR+".join([f"cat:{c}" for c in self.categories])
        url = f"https://export.arxiv.org/api/query?search_query={cat_query}&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"

        xml_data = None
        try:
            import requests
            resp = requests.get(url, headers={'User-Agent': 'PaperSnapBot/1.0'}, timeout=15)
            if resp.status_code == 200:
                xml_data = resp.content
                logger.info("Successfully fetched ArXiv feed using requests.")
        except Exception as req_err:
            logger.warning(f"requests fetch failed ({req_err}), trying urllib Atom API...")

        if xml_data is None:
            return self._fetch_via_atom_api(max_results)

        try:
            root = ET.fromstring(xml_data)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            results = []
            for entry in root.findall('atom:entry', ns):
                raw_id = entry.find('atom:id', ns).text.strip()
                arxiv_id = raw_id.split('/')[-1]
                if 'v' in arxiv_id:
                    arxiv_id = arxiv_id.split('v')[0]

                title = entry.find('atom:title', ns).text.replace("\n", " ").strip()
                summary = entry.find('atom:summary', ns).text.replace("\n", " ").strip()
                published = entry.find('atom:published', ns).text[:10]
                
                authors_list = [a.find('atom:name', ns).text for a in entry.findall('atom:author', ns)]
                authors = ", ".join(authors_list[:5])
                if len(authors_list) > 5:
                    authors += " et al."

                results.append({
                    "arxiv_id": arxiv_id,
                    "title": title,
                    "authors": authors,
                    "published": published,
                    "summary": summary,
                    "url": f"https://arxiv.org/abs/{arxiv_id}",
                    "categories": self.categories
                })
            logger.info(f"Successfully parsed {len(results)} papers from ArXiv feed.")
            return results
        except Exception as ex:
            logger.error(f"Error parsing ArXiv XML feed: {ex}")
            return []


    def _fetch_via_atom_api(self, max_results: int = 10) -> List[Dict[str, Any]]:
        cat_query = "+OR+".join([f"cat:{c}" for c in self.categories])
        url = f"https://export.arxiv.org/api/query?search_query={cat_query}&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"
        
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'PaperSnapBot/1.0'})
            
            context = None
            try:
                import ssl
                context = ssl._create_unverified_context()
            except Exception as e:
                logger.warning(f"Could not initialize ssl context ({e}), proceeding with standard urlopen.")

            if context:
                resp_ctx = urllib.request.urlopen(req, context=context, timeout=15)
            else:
                resp_ctx = urllib.request.urlopen(req, timeout=15)

            with resp_ctx as response:
                xml_data = response.read()

            root = ET.fromstring(xml_data)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            results = []
            for entry in root.findall('atom:entry', ns):
                raw_id = entry.find('atom:id', ns).text.strip()
                arxiv_id = raw_id.split('/')[-1]
                if 'v' in arxiv_id:
                    arxiv_id = arxiv_id.split('v')[0]

                title = entry.find('atom:title', ns).text.replace("\n", " ").strip()
                summary = entry.find('atom:summary', ns).text.replace("\n", " ").strip()
                published = entry.find('atom:published', ns).text[:10]
                
                authors_list = [a.find('atom:name', ns).text for a in entry.findall('atom:author', ns)]
                authors = ", ".join(authors_list[:5])
                if len(authors_list) > 5:
                    authors += " et al."

                results.append({
                    "arxiv_id": arxiv_id,
                    "title": title,
                    "authors": authors,
                    "published": published,
                    "summary": summary,
                    "url": f"https://arxiv.org/abs/{arxiv_id}",
                    "categories": self.categories
                })
            logger.info(f"Successfully fetched {len(results)} papers via ArXiv XML API.")
            return results
        except Exception as ex:
            logger.warning(f"Error fetching from ArXiv HTTPS XML API: {ex}, attempting HTTP fallback...")
            return self._fetch_via_atom_http_fallback(max_results)

    def _fetch_via_atom_http_fallback(self, max_results: int = 10) -> List[Dict[str, Any]]:
        cat_query = "+OR+".join([f"cat:{c}" for c in self.categories])
        url = f"http://export.arxiv.org/api/query?search_query={cat_query}&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'PaperSnapBot/1.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                xml_data = response.read()

            root = ET.fromstring(xml_data)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            results = []
            for entry in root.findall('atom:entry', ns):
                raw_id = entry.find('atom:id', ns).text.strip()
                arxiv_id = raw_id.split('/')[-1]
                if 'v' in arxiv_id:
                    arxiv_id = arxiv_id.split('v')[0]

                title = entry.find('atom:title', ns).text.replace("\n", " ").strip()
                summary = entry.find('atom:summary', ns).text.replace("\n", " ").strip()
                published = entry.find('atom:published', ns).text[:10]
                
                authors_list = [a.find('atom:name', ns).text for a in entry.findall('atom:author', ns)]
                authors = ", ".join(authors_list[:5])
                if len(authors_list) > 5:
                    authors += " et al."

                results.append({
                    "arxiv_id": arxiv_id,
                    "title": title,
                    "authors": authors,
                    "published": published,
                    "summary": summary,
                    "url": f"https://arxiv.org/abs/{arxiv_id}",
                    "categories": self.categories
                })
            logger.info(f"Successfully fetched {len(results)} papers via ArXiv HTTP XML API.")
            return results
        except Exception as ex:
            logger.error(f"Error fetching from ArXiv HTTP XML API: {ex}")
            return []

    def fetch_paper_by_id(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch full details and abstract for a specific ArXiv ID.
        """
        try:
            import arxiv
            search = arxiv.Search(id_list=[arxiv_id])
            client = arxiv.Client()
            results = list(client.results(search))
            if results:
                result = results[0]
                authors = ", ".join([a.name for a in result.authors[:5]])
                if len(result.authors) > 5:
                    authors += " et al."
                return {
                    "arxiv_id": arxiv_id,
                    "title": result.title.replace("\n", " ").strip(),
                    "authors": authors,
                    "published": result.published.strftime("%Y-%m-%d") if result.published else "",
                    "summary": result.summary.replace("\n", " ").strip(),
                    "url": f"https://arxiv.org/abs/{arxiv_id}",
                    "categories": result.categories
                }
        except Exception as e:
            logger.warning(f"Failed to fetch paper by ID {arxiv_id} via arxiv SDK ({e}).")
        return None




