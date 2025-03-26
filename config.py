import os
import logging
from dotenv import load_dotenv
import google.generativeai as genai

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY_EX")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")

# Configure Gemini AI
genai.configure(api_key=GEMINI_API_KEY)

# Wikipedia API setup
USER_AGENT = os.getenv("USER_AGENT")
WIKI_HEADERS = {"User-Agent": USER_AGENT}