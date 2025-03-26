import re
import requests

def fetch_wikipedia_plaintext(title):
    """Fetches Wikipedia page content in plaintext format using the MediaWiki API."""
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "titles": title,
        "explaintext": True  # Get raw text instead of HTML or wikitext
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    
    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        return page.get("extract", "")
    return ""

def clean_wikipedia_text(text):
    """
    Cleans Wikipedia article extracts for AI models:
    - Removes section headers (`== Title ==`).
    - Removes inline citations after punctuation (`. 867`, `: 18–19 : §1.5`).
    - Preserves valid colons (`The total population: 8 billion`).
    - Converts LaTeX `{\\displaystyle ...}` to `$...$`.
    - Converts LaTeX `{\\textstyle ...}` to `$$...$$`.
    - Ensures proper bracket matching.
    - Normalizes whitespace and removes extra newlines.
    """
    # Remove Wikipedia-style section headers (e.g., '== History ==', '=== Details ===')
    text = re.sub(r"(?m)^={2,6}\s*(.*?)\s*={2,6}$", "", text)

    # Remove inline citations (e.g., `. 867`, `: 18–19 : §1.5`)
    text = re.sub(r"([.:])\s*((§?\d+(\.\d+)?(?:–\d+)?)(\s*:\s*(§?\d+(\.\d+)?(?:–\d+)?))*)", r"\1", text)

    # Remove any leftover colons that are not followed by a letter (e.g., `:.` or `: `)
    text = re.sub(r":\s+(?=[^a-zA-Z])", "", text)

    # Convert LaTeX-style inline expressions to `$...$`
    text = re.sub(r"{\\displaystyle\s+([^}]+)}", r"$\1$", text)

    # Convert LaTeX-style block equations to `$$ ... $$`
    text = re.sub(r"{\\textstyle\s+([^}]+)}", r"$$\1$$", text)

    # Ensure matching brackets in LaTeX expressions
    text = re.sub(r"\$([^{]*){([^}]*)\$", r"$\1{\2}$", text)  # Fix `{}` placement
    text = re.sub(r"\${(.*?)}\$", r"$\1$", text)  # Remove unnecessary `{}` around equations

    # Fix fractions and LaTeX functions
    text = text.replace(r"\tfrac", r"\frac")  # Convert `\tfrac` to `\frac`
    text = text.replace(r"\displaystyle", "")  # Remove redundant `\displaystyle`

    # Normalize whitespace (replace multiple spaces/newlines with a single space)
    text = re.sub(r"\s+", " ", text).strip()
    
    return text

def split_into_chunks(text, max_length=500):
    """Splits cleaned Wikipedia text into AI-friendly chunks."""
    sentences = re.split(r'(?<=[.!?]) +', text)  # Split by sentence
    chunks, current_chunk = [], []
    
    for sentence in sentences:
        if sum(len(s) for s in current_chunk) + len(sentence) > max_length:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
        current_chunk.append(sentence)
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks

# Example usage
if __name__ == "__main__":
    title = "Quantum_entanglement"  # Example Wikipedia page
    raw_text = fetch_wikipedia_plaintext(title)
    cleaned_text = clean_wikipedia_text(raw_text)
    chunks = split_into_chunks(cleaned_text)
    
    # Save cleaned content
    with open("cleaned_wikipedia_text.txt", "w", encoding="utf-8") as f:
        f.write(cleaned_text)
    
    # Print AI-friendly chunks
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i+1}:\n{chunk}\n")