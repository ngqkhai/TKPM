import logging
from .query_refiner import refine_query_with_gemini
from .relevance_scorer import is_relevant_page_gemini
from .wikipedia_api import search_wikipedia, get_wikipedia_content

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