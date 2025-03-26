import re
import requests
import subprocess
import logging

def fetch_wikipedia_mediawiki(title):
    """Fetch Wikipedia page content in MediaWiki format with error handling."""
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "prop": "revisions",
        "titles": title,
        "rvprop": "content",
        "rvslots": "main"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        pages = data.get("query", {}).get("pages", {})

        for page_id, page_data in pages.items():
            if "missing" in page_data:
                logging.warning(f"Page '{title}' not found on Wikipedia.")
                return None
            revisions = page_data.get("revisions", [])
            if revisions:
                return revisions[0].get("slots", {}).get("main", {}).get("*", "")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching Wikipedia data: {e}")
        return None

    return None  # If no valid content is found

# Example usage
if __name__ == "__main__":
    title = "Quantum_entanglement"
    content = fetch_wikipedia_mediawiki(title)
    
    if content:
        print("✅ Successfully fetched Wikipedia content!")
        print(content[:500])  # Preview first 500 characters
    else:
        print("❌ No content retrieved.")

def convert_mediawiki_to_markdown(input_file, output_file):
    """Converts MediaWiki text to Markdown using Pandoc."""
    subprocess.run(["pandoc", "-f", "mediawiki", "-t", "markdown", "-o", output_file, input_file], check=True)

def clean_markdown(content):
        # Handle backtick-enclosed MediaWiki content - need to do this first
        content = re.sub(r'``\{=mediawiki\}', '', content)
        content = re.sub(r'``(?:\{=mediawiki\})?', '', content)
        content = re.sub(r'`\{=mediawiki\}', '', content)
        content = re.sub(r'`(?:\{=mediawiki\})?', '', content)
        
        # Remove all image references completely
        content = re.sub(r'!\[.*?\]\(.*?\)(?:\{.*?\})?', '', content)
        content = re.sub(r'!\[\[.*?\]\].*?(?:\{.*?\})?', '', content)
        
        # Extract text from wiki-links - preserve text only
        content = re.sub(r'\[(.*?)\]\([^)]*?\)(?:\{\.wikilink\})?', r'\1', content)
        
        # Remove incomplete reference formats like "position")"
        content = re.sub(r' "([^"]+)"\)', r'', content)
        
        # Remove HTML comments
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        
        # Convert MediaWiki math to Markdown math format
        content = re.sub(r'\{\{math\|(.*?)\}\}', r'$\1$', content)
        
        # Remove MediaWiki templates but preserve math
        content = re.sub(r'\{\{(?!math\|).*?\}\}', '', content)
        
        # Remove additional MediaWiki elements and formatting remnants
        content = re.sub(r'\{=mediawiki\}', '', content)
        content = re.sub(r'\{\.wikilink\}', '', content)
        
        # Remove width/height attributes in images
        content = re.sub(r'\{width="\d+".*?height="\d+"\}', '', content)
        
        # Clean up any leftover empty references
        content = re.sub(r'\(\s*\)', '', content)
        
        # Remove footnotes references
        content = re.sub(r'\[\^.*?\](?:\{.*?\})?', '', content)
        
        # Remove sections that aren't needed for AI processing
        content = re.sub(r'## References[\s\S]*?(?=##|$)', '', content)
        content = re.sub(r'## External links[\s\S]*?(?=##|$)', '', content)
        content = re.sub(r'## See also[\s\S]*?(?=##|$)', '', content)
        content = re.sub(r'## Further reading[\s\S]*?(?=##|$)', '', content)
        content = re.sub(r'- \[.*?\]\(.*?\)', '', content)  # Remove remaining list items with links
        
        # Fix spacing issues that might have been created by removals
        content = re.sub(r' +', ' ', content)  # Replace multiple spaces with single space
        
        # More aggressive newline normalization - first pass
        content = re.sub(r'\n{2,}', '\n\n', content)  # Limit to max 2 consecutive newlines
        
        # Process the content paragraph by paragraph instead of line by line
        paragraphs = content.split('\n\n')
        cleaned_paragraphs = []
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            
            # Skip paragraphs that are just formatting remnants
            if not paragraph or re.match(r'^(?:\{.*?\}|``|`)$', paragraph):
                continue
            
            # Handle headers specially to ensure they have proper spacing
            if paragraph.startswith('#'):
                # Ensure headers have a blank line before them (except for the first one)
                if cleaned_paragraphs:
                    cleaned_paragraphs.append('')
                cleaned_paragraphs.append(paragraph)
                continue
                
            # Clean up the paragraph further
            lines = paragraph.split('\n')
            cleaned_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Fix lines that end with unclosed quotes or partial references
                line = re.sub(r'"$', '', line)
                # Fix lines that might've been cut off by regex operations
                line = re.sub(r'^\s*and\s+', '', line)
                line = re.sub(r'^\s*,\s*', '', line)
                cleaned_lines.append(line)
            
            # Join cleaned lines of the paragraph with single spaces
            if cleaned_lines:
                cleaned_paragraphs.append(' '.join(cleaned_lines))
        
        # Recombine paragraphs with proper spacing
        final_content = '\n\n'.join(cleaned_paragraphs)
        
        # Final newline normalization
        final_content = re.sub(r'\n{3,}', '\n\n', final_content)
        return final_content
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
    mediawiki_text = fetch_wikipedia_mediawiki(title)
    # Save raw MediaWiki format
    with open("wikipedia_mediawiki.txt", "w", encoding="utf-8") as f:
        f.write(mediawiki_text)
    
    # Convert MediaWiki to Markdown using Pandoc
    convert_mediawiki_to_markdown("wikipedia_mediawiki.txt", "wikipedia_markdown.md")
    
    # Read converted Markdown
    with open("wikipedia_markdown.md", "r", encoding="utf-8") as f:
        markdown_text = f.read()
    
    # Clean Markdown
    cleaned_text = clean_markdown(markdown_text)
    
    # Save cleaned content
    with open("cleaned_wikipedia_text.txt", "w", encoding="utf-8") as f:
        f.write(cleaned_text)
    
    # Split into chunks for AI processing
    chunks = split_into_chunks(cleaned_text)
    
    # Print AI-friendly chunks
    for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
        print(f"Chunk {i+1}:\n{chunk}\n")
