import time
import logging
import google.generativeai as genai
from config import GEMINI_MODEL

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