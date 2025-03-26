import requests
import os
import time
from dotenv import load_dotenv
import google.generativeai as genai
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY_EX")
GEMINI_MODEL = "gemini-2.0-flash-lite"

# Configure Gemini AI
genai.configure(api_key=GEMINI_API_KEY)

# Wikipedia API setup
USER_AGENT = "ScienceScraperBot/1.0 (https://github.com/ngqkhai)"
HEADERS = {"User-Agent": USER_AGENT}


### --- Step 1: AI-Optimized Wikipedia Query Refinement --- ###
def refine_query_with_gemini(query, max_retries=3):
    """
    Uses Gemini AI to convert a user question into a concise, Wikipedia-friendly search phrase.
    The prompt is designed to work across diverse query types and knowledge domains.
    If a 429 quota error occurs, the function waits 60 seconds and retries.
    Return only the refined search phrase as plain text.
    """
    model = genai.GenerativeModel(GEMINI_MODEL)
    prompt = f"""
Transform this user question into the optimal Wikipedia search term:

"{query}"

Rules to follow:
1. For "what is" questions: Use the subject noun phrase (e.g., "What is quantum computing?" → "Quantum computing")
2. For "who" questions: Focus on the achievement or concept (e.g., "Who discovered gravity?" → "Discovery of gravity")
3. For "why/how" questions: Extract the core phenomenon (e.g., "Why is the sky blue?" → "Sky blue phenomenon")
4. For cause/effect questions: Focus on the effect (e.g., "What causes earthquakes?" → "Earthquakes")
5. Follow Wikipedia's naming pattern – typically concise noun phrases.
6. Limit to 1-4 words unless additional context is necessary.
7. Prefer technical terms over colloquial expressions.
8. Do NOT include names, dates, or direct answers.

Output ONLY the search term as plain text.
"""
    attempt = 0
    while attempt <= max_retries:
        try:
            response = model.generate_content(prompt)
            refined = response.text.strip()
            logging.info(f"Refined query: '{refined}'")
            return refined
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg:
                logging.warning(f"Gemini quota exceeded. Sleeping 60s before retrying... (Attempt {attempt+1}/{max_retries})")
                time.sleep(60)
                attempt += 1
                continue
            else:
                logging.error(f"Gemini error during query refinement: {e}")
                break
    return query  # Fallback to original query if Gemini repeatedly fails


### --- Step 2: Wikipedia Search (Standard Search API) --- ###
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
            response = requests.get(url, headers=HEADERS, params=params, timeout=10)
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


### --- Step 3: Fetch Wikipedia Content + Categories (Disambiguation Check) --- ###
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
            response = requests.get(url, headers=HEADERS, params=params, timeout=10)
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


### --- Step 4: AI Validation (Gemini) for Best Match --- ###
def is_relevant_page_gemini(query, wiki_title, wiki_summary, max_retries=3):
    """
    Uses Gemini AI to assess relevance between the user query and Wikipedia content.
    Returns a confidence score between 0.0 and 1.0.
    If a 429 error occurs, waits 60 seconds and retries.
    """
    model = genai.GenerativeModel(GEMINI_MODEL)
    summary_preview = wiki_summary[:300] + ("..." if len(wiki_summary) > 300 else "")
    prompt = f"""
You are a relevance scoring algorithm that evaluates how well a Wikipedia article answers a user's question.

USER QUESTION: "{query}"
WIKIPEDIA ARTICLE TITLE: "{wiki_title}"
WIKIPEDIA ARTICLE EXCERPT: "{summary_preview}"

Score how directly this article answers the user's question:
- 1.0: Perfectly answers the question.
- 0.8-0.9: Highly relevant.
- 0.6-0.7: Partially addresses the question.
- 0.4-0.5: Minimally relevant.
- 0.0: Completely irrelevant.

Output ONLY a single decimal score between 0.0 and 1.0.
"""
    attempt = 0
    while attempt <= max_retries:
        try:
            response = model.generate_content(prompt)
            score_text = response.text.strip()
            score_text = ''.join(c for c in score_text if c.isdigit() or c == '.')
            score = float(score_text)
            score = max(0.0, min(score, 1.0))
            return score
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg:
                logging.warning(f"Gemini relevance quota exceeded. Sleeping 60s before retrying... (Attempt {attempt+1}/{max_retries})")
                time.sleep(60)
                attempt += 1
                continue
            logging.error(f"Gemini relevance scoring error: {e}")
            break
    return 0.0


### --- Step 5: Fetch Best Wikipedia Page --- ###
def fetch_best_wikipedia_page(query):
    """
    Enhanced pipeline for finding the most relevant Wikipedia page.
    Combines:
      1. Query refinement using Gemini.
      2. Wikipedia search using the standard search API.
      3. Content fetching with disambiguation filtering.
      4. AI-based relevance validation.
    Returns a dictionary with the best matching Wikipedia page or an error message.
    """
    refined_query = refine_query_with_gemini(query)
    logging.info(f"Refined Query: '{refined_query}'")
    
    titles = search_wikipedia(refined_query)
    if not titles:
        logging.warning("Refined query returned no results, trying original query...")
        titles = search_wikipedia(query)
        if not titles:
            return {"error": "No Wikipedia pages found for this query."}
    
    logging.info(f"Wikipedia Results: {titles}")
    
    candidates = []
    for title in titles:
        wiki_title, wiki_summary = get_wikipedia_content(title)
        if wiki_title and wiki_summary:
            relevance_score = is_relevant_page_gemini(query, wiki_title, wiki_summary)
            logging.info(f"'{wiki_title}' - Relevance: {relevance_score:.2f}")
            candidates.append((wiki_title, wiki_summary, relevance_score))
    
    candidates.sort(key=lambda x: x[2], reverse=True)
    
    if candidates and candidates[0][2] >= 0.7:
        best_match = candidates[0]
        logging.info(f"Best Match: '{best_match[0]}' (score: {best_match[2]:.2f})")
        return {"title": best_match[0], "content": best_match[1], "score": best_match[2]}
    
    if candidates:
        best_available = candidates[0]
        logging.warning(f"No highly relevant matches. Using best available: '{best_available[0]}' (score: {best_available[2]:.2f})")
        return {"title": best_available[0], "content": best_available[1], "score": best_available[2]}
    
    return {"error": "No relevant Wikipedia content found."}


### --- Example Usage --- ###
if __name__ == "__main__":
    test_queries = [
        "Who discovered gravity?",
        "Why do we dream?",
        "How does photosynthesis work?",
        "What is artificial intelligence?",
        "Why is the ocean salty?",
        "How do vaccines work?",
        "What causes earthquakes?",
        "What is quantum mechanics?",
        "Why do we have seasons?",
        "What is consciousness?",
        "Why do people lie?",
        "What is the meaning of life?",
        "Why do humans have emotions?",
        "How does memory work?",
        "How does the internet work?",
        "What is machine learning?",
        "Who invented the computer?",
        "Why is Python popular?",
        "What is blockchain?",
        "Why did the Roman Empire fall?",
        "Who was the first president of the USA?",
        "What caused World War II?",
        "What is the oldest civilization?",
        "Why was the Great Wall of China built?",
        "Who is the greatest painter of all time?",
        "What is classical music?",
        "How did hip-hop start?",
        "What is Shakespeare known for?",
        "Why are movies called 'films'?",
        "Why do we have fingerprints?",
        "How do birds fly?",
        "Why do some people have allergies?",
        "What is the function of the liver?",
        "How does DNA work?",
        "Why is the sky dark at night?",
        "What is a black hole?",
        "How was the universe formed?",
        "Why do planets orbit the sun?",
        "What is dark matter?"
    ]
    for query in test_queries:
            logging.info(f"\nUser Query: {query}")
            result = fetch_best_wikipedia_page(query)
            if "error" in result:
                logging.error(result["error"])
                file.write(f"{query}\n")
            else:
                if result.get("score", 0) < 0.7:
                    file.write(f"{query}\n")
                logging.info(f"Title: {result['title']}")
                logging.info(f"Relevance Score: {result.get('score', 0):.2f}")
                logging.info(f"Content Preview: {result['content'][:500]}...\n")

    logging.info(f"Failed queries saved in '{output_file}'.")
