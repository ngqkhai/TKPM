from data_collection.wiki_search_pipeline import fetch_best_wikipedia_page

def main():
    """
    Main entry point for the Wikipedia search application.
    Demonstrates the functionality with example queries.
    Writes the results to a text file.
    """
    test_queries = [
        "What is quantum entanglement?",
    ]
    
    with open("wikipedia_search_results.txt", "w") as file:  # Open the file to write
        for query in test_queries:
            file.write("\n" + "="*50 + "\n")
            file.write(f"USER QUERY: {query}\n")
            file.write("="*50 + "\n")
            
            result = fetch_best_wikipedia_page(query)
            
            if "error" in result:
                file.write(f"ERROR: {result['error']}\n")
            else:
                file.write(f"TITLE: {result['title']}\n")
                # file.write(f"RELEVANCE: {result['score']:.2f}\n")
                file.write("\nCONTENT PREVIEW:\n")
                file.write("-"*50 + "\n")
                
                # Show first 300 characters of content
                preview = result['content'][:300] + "..." if len(result['content']) > 300 else result['content']
                file.write(preview + "\n")
                file.write("-"*50 + "\n")


if __name__ == "__main__":
    main()
