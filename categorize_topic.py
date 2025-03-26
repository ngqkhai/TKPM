import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve API key securely
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY is missing. Set it in the environment variables or .env file.")

# Configure Google Gemini API
genai.configure(api_key=API_KEY)

# List of general scientific topics
SCIENTIFIC_TOPICS = {
    "Physics", "Astronomy", "Biology", "AI & Computer Science", "Medicine",
    "Chemistry", "Earth Science", "Mathematics", "Engineering", "Environmental Science",
    "Neuroscience", "Social Sciences", "Psychology", "Genetics", "Material Science",
    "Energy Science", "Robotics", "Climate Science", "Geology", "Oceanography"
}

def classify_topic_gemini(query):
    """Classifies a query into a scientific topic using Gemini with error handling."""
    if not query.strip():
        return "Unknown"

    prompt = (
        f"Classify the following query into one of these scientific topics: {', '.join(SCIENTIFIC_TOPICS)}. "
        f"If none match, return 'Unknown'.\nQuery: {query}\nTopic:"
    )

    try:
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        response = model.generate_content(prompt)

        # Ensure response is valid
        if not response or not response.text:
            return "Unknown"

        topic = response.text.strip()
        print(topic)
        # Validate the response
        if topic in SCIENTIFIC_TOPICS:
            return topic
        return "Unknown"

    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return "Unknown"
