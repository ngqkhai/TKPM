import time
import logging
import google.generativeai as genai
from config import GEMINI_MODEL

def is_relevant_page_gemini(query, wiki_title, wiki_summary, max_retries=3):
    """
    Uses Gemini AI to assess relevance between the user query and Wikipedia content.
    Returns a confidence score between 0.0 and 1.0.
    If a 429 error occurs, waits 60 seconds and retries.
    """
    model = genai.GenerativeModel(GEMINI_MODEL)
    summary_preview = wiki_summary[:500] + ("..." if len(wiki_summary) > 500 else "")
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