from abc import ABC, abstractmethod
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()
NATURE_API_KEY = os.getenv("NATURE_API_KEY")
# -----------------------------
# Abstract Base Class
# -----------------------------
class DataRetriever(ABC):
    @abstractmethod
    def search(self, query: str, max_results: int = 10):
        """Search for data using a query string."""
        pass

# -----------------------------
# PubMed Retriever using NCBI E-utilities
# -----------------------------
class PubMedRetriever(DataRetriever):
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

    def search(self, query: str, max_results: int = 10):
        """
        Optimized search for PubMed:
        - Uses field-specific search (Title/Abstract)
        - Filters for journal articles
        - Limits to recent publications (last 5 years)
        - Sorts by relevance via API parameters
        """
        formatted_query = f"({query})[Title/Abstract] AND (journal article[Publication Type])"
        params = {
            "db": "pubmed",
            "term": formatted_query,
            "retmode": "json",
            "retmax": max_results,
            "sort": "relevance",  # API-driven relevance sorting
            "datetype": "pdat",
            "reldate": 365 * 5  # Limit to the last 5 years
        }

        try:
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            id_list = data.get("esearchresult", {}).get("idlist", [])
            return id_list
        except requests.RequestException as e:
            print(f"Error retrieving PubMed data: {e}")
            return []

# -----------------------------
# arXiv Retriever using its API (returns Atom XML)
# -----------------------------
class ArxivRetriever(DataRetriever):
    BASE_URL = "http://export.arxiv.org/api/query"

    def search(self, query: str, max_results: int = 10):
        """
        Optimized search for arXiv:
        - Searches title and abstract using exact phrase matching
        - Constructs a query using Boolean operators for higher relevance
        - Sorts results by publication date (latest first)
        """
        # Using field-specific query syntax to target title and abstract
        formatted_query = f'ti:"{query}" OR abs:"{query}"'
        params = {
            "search_query": formatted_query,
            "start": 0,
            "max_results": max_results
        }

        try:
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
            root = ET.fromstring(response.content)

            results = []
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            for entry in root.findall("atom:entry", ns):
                title = entry.find("atom:title", ns).text.strip()
                abstract = entry.find("atom:summary", ns).text.strip()
                published = entry.find("atom:published", ns).text.strip()

                results.append({
                    "title": title,
                    "abstract": abstract,
                    "published": published
                })

            # Sort results by publication date (assuming ISO date format, latest first)
            results = sorted(results, key=lambda x: x["published"], reverse=True)
            return results
        except requests.RequestException as e:
            print(f"Error retrieving arXiv data: {e}")
            return []
        except ET.ParseError as pe:
            print(f"Error parsing arXiv XML: {pe}")
            return []

# -----------------------------
# Nature Retriever using Springer API
# -----------------------------
class NatureRetriever(DataRetriever):
    BASE_URL = "https://api.springernature.com/openaccess/json"
    API_KEY = NATURE_API_KEY  # Replace with your actual API key

    def search(self, query: str, max_results: int = 10):
        """
        Optimized search for Nature/Springer Open Access:
        - Uses Boolean search to target title and abstract fields
        - Requests results sorted by publication date from the API
        - Post-processes to filter and sort if needed
        """
        params = {
            "api_key": self.API_KEY,
            "q": f"title:{query} OR abstract:{query}",
            "p": max_results,
            "s": "date"  # Let the API sort by publication date
        }

        try:
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            records = data.get("records", [])

            results = []
            for record in records:
                title = record.get("title")
                abstract = record.get("abstract")
                publication_date = record.get("publicationDate")
                journalTitle = record.get("journalTitle")
                doi = record.get("doi")

                results.append({
                    "title": title,
                    "abstract": abstract,
                    "publicationDate": publication_date,
                    "journalTitle": journalTitle,
                    "doi": doi
                })

            # Sort by publication date (latest first)
            results = sorted(results, key=lambda x: x["publicationDate"], reverse=True)
            return results
        except requests.RequestException as e:
            print(f"Error retrieving Nature data: {e}")
            return []
        except ValueError as ve:
            print(f"Error parsing Nature JSON: {ve}")
            return []

# -----------------------------
# Main Driver Function to Test Retrievers
# -----------------------------
def main():
    query = "CRISPR gene editing"
    
    # PubMed
    pubmed = PubMedRetriever()
    pubmed_ids = pubmed.search(query)
    print("PubMed IDs:")
    for pid in pubmed_ids:
        print(f" - {pid}")

    # arXiv
    arxiv = ArxivRetriever()
    arxiv_results = arxiv.search(query)
    print("\narXiv Titles:")
    for result in arxiv_results:
        print(f" - {result['title']} (Published: {result['published']})")

    # Nature/Springer
    # nature = NatureRetriever()
    # nature_results = nature.search(query, max_results=5)
    # print("\nNature/Springer Open Access Articles:")
    # for idx, record in enumerate(nature_results, 1):
    #     print(f"{idx}. Title: {record.get('title')}")
    #     print(f"   DOI: {record.get('doi')}")
    #     print(f"   Abstract: {record.get('abstract')}")
    #     print(f"   Publication Date: {record.get('publicationDate')}")
    #     print(f"   Journal Title: {record.get('journalTitle')}\n")

if __name__ == "__main__":
    main()
