from abc import ABC, abstractmethod
import requests
from bs4 import BeautifulSoup

# Abstract Base Class
class DataSource(ABC):
    """Abstract base class for data sources."""
    
    def __init__(self, url):
        self.url = url

    @abstractmethod
    def fetch_data(self):
        """Method to fetch data. Must be implemented by subclasses."""
        pass

# API Source Class
class APISource(DataSource):
    """Handles data fetching from API-based sources."""
    
    def __init__(self, url, api_key=None, params=None):
        super().__init__(url)
        self.api_key = api_key
        self.params = params if params else {}

    def fetch_data(self):
        """Fetch data using an API request."""
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        print(headers)
        response = requests.get(self.url, headers=headers, params=self.params)
        
        if response.status_code == 200:
            return response.json()  # Assuming JSON response
        else:
            return {"error": f"Failed to fetch data: {response.status_code}"}

# Scraper Source Class
class ScraperSource(DataSource):
    """Handles web scraping for sources without APIs."""
    
    def fetch_data(self):
        """Fetch data using web scraping."""
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(self.url, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            return self.parse_html(soup)
        else:
            return {"error": f"Failed to scrape data: {response.status_code}"}

    def parse_html(self, soup):
        """Extract relevant data from the HTML."""
        articles = []
        for article in soup.find_all("h2"):  # Adjust selector based on site structure
            title = article.get_text()
            link = article.find("a")["href"] if article.find("a") else None
            articles.append({"title": title, "link": link})
        return articles
# Define API-based and Scraping-based sources
TOPIC_TO_SOURCES = {
    "Physics": [APISource("https://api.nasa.gov/planetary/apod", api_key="0sieqt3dNxFMGiy05pceHmTnbMZCZeWLe5QtOFUh")],
    "Astronomy": [ScraperSource("https://hubblesite.org/news")],
    "Biology": [APISource("https://pubmed.ncbi.nlm.nih.gov", params={"term": "genetics"})]
}

# Fetch data for a topic
def fetch_topic_data(topic):
    if topic in TOPIC_TO_SOURCES:
        for source in TOPIC_TO_SOURCES[topic]:
            data = source.fetch_data()
            print(f"Data from {source.url}:", data)
    else:
        print("No sources found for this topic.")

# Example Usage
fetch_topic_data("Physics")
fetch_topic_data("Astronomy")
