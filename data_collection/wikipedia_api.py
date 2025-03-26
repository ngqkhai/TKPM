import requests
import time
import logging
from config import WIKI_HEADERS

def search_wikipedia(query, max_retries=2):
    """
    Searches Wikipedia for relevant page titles using the standard search API.
    Returns a list of up to 5 article titles.
    Includes retry logic for better resilience.
    """
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": query,
        "srlimit": 5,
    }
    
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, headers=WIKI_HEADERS, params=params, timeout=10)
            logging.info(f"Search URL: {response.url}")
            if response.status_code == 200:
                search_results = response.json().get("query", {}).get("search", [])
                return [res["title"] for res in search_results]
            elif response.status_code == 429:
                wait_time = 2 * (attempt + 1)
                logging.warning(f"Wikipedia search rate limited. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
            logging.error(f"Wikipedia search failed with status: {response.status_code}")
            return []
        except requests.exceptions.RequestException as e:
            if attempt < max_retries:
                logging.warning(f"Request error: {e}. Retrying...")
                continue
            logging.error(f"Wikipedia search request error: {e}")
            return []
    
    return []


def get_wikipedia_content(title, max_retries=2):
    """
    Retrieves the full content and categories for a given Wikipedia article.
    Filters out disambiguation pages.
    Returns (title, content) if valid, else (None, None).
    Includes retry logic for better resilience.
    """
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts|categories",
        "explaintext": True,
        "titles": title
    }
    
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, headers=WIKI_HEADERS, params=params, timeout=10)
            logging.info(f"Content URL: {response.url}")
            if response.status_code == 200:
                data = response.json().get("query", {}).get("pages", {})
                for page in data.values():
                    extract = page.get("extract", "")
                    categories = [cat["title"].lower() for cat in page.get("categories", [])]
                    if any("disambiguation" in cat for cat in categories):
                        return None, None
                    return title, extract
                return None, None
            elif response.status_code == 429:
                wait_time = 2 * (attempt + 1)
                logging.warning(f"Wikipedia content fetch rate limited. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
            logging.error(f"Wikipedia content fetch failed with status: {response.status_code}")
            return None, None
        except requests.exceptions.RequestException as e:
            if attempt < max_retries:
                continue
            logging.error(f"Wikipedia content request error: {e}")
            return None, None
    
    return None, None