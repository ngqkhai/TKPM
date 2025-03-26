import requests
from preprocess_input import preprocess_query
from categorize_topic import classify_topic_gemini
import time

# Wikipedia API setup
USER_AGENT = "ScienceArticleScraperBot/1.0 (https://github.com/ngqkhai)"
HEADERS = {"User-Agent": USER_AGENT}

def search_wikipedia(query):
    """
    Searches Wikipedia for the most relevant page title based on the query.
    Returns the best match page title.
    """
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": query
    }

    response = requests.get(url, headers=HEADERS, params=params)
    data = response.json()

    if "query" in data and "search" in data["query"]:
        return data["query"]["search"][0]["title"]  # Return the top search result

    return None

def get_wikipedia_content(title):
    """
    Retrieves the full content of a Wikipedia page by its title.
    """
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "explaintext": True,
        "titles": title
    }

    response = requests.get(url, headers=HEADERS, params=params)
    data = response.json()

    pages = data.get("query", {}).get("pages", {})
    page_content = next(iter(pages.values()), {}).get("extract", "")

    return page_content if page_content else "Content not found."

# Main function to get Wikipedia content for a query
def fetch_scientific_content(query):
    # cleaned_query = preprocess_query(query)
    cleaned_query = query
    print(cleaned_query)
    detected_topic = classify_topic_gemini(cleaned_query)

    wikipedia_title = search_wikipedia(cleaned_query)
    if wikipedia_title:
        content = get_wikipedia_content(wikipedia_title)
        return {"title": wikipedia_title, "content": content}

    return {"error": "No relevant Wikipedia page found."}

# Example usage
query = "What is quantum entanglement?"
data = fetch_scientific_content(query)
print(f"Title: {data.get('title', 'Not found')}\n")
print(data.get("content", "No content retrieved."))
