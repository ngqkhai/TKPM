import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Load NLTK tools
# nltk.download("stopwords")
# nltk.download("wordnet")

stop_words = set(stopwords.words("english"))
lemmatizer = WordNetLemmatizer()

# Important words that must be preserved (question words + scientific terms)
important_words = {"why", "how", "what", "who", "when", "where", "which"}

# Allowed scientific symbols (common in equations & science papers)
scientific_symbols = set("°%μΩ±≤≥≠−+*/")

def preprocess_query(query):
    """Preprocess a scientific query for effective search."""
    # Convert to lowercase & remove extra spaces
    query = query.lower().strip()

    # Keep only letters, numbers, spaces, and allowed scientific symbols
    query = "".join(c for c in query if c.isalnum() or c.isspace() or c in scientific_symbols)

    # Tokenize the query
    words = query.split()

    # Lemmatize and filter stopwords (except important question words)
    processed_words = [
        lemmatizer.lemmatize(word) 
        for word in words 
        if word in important_words or word not in stop_words
    ]

    # Reconstruct the cleaned query
    cleaned_query = " ".join(processed_words)

    # Handle edge case: empty query after cleaning
    return cleaned_query if cleaned_query else "Invalid input: Please enter a relevant scientific query."