from data_collection.wiki_search_pipeline import fetch_best_wikipedia_page
def main():
    """
    Main entry point for the Wikipedia search application.
    Demonstrates the functionality with example queries.
    """
    test_queries = [
        "Who discovered gravity?",
        "Why do we dream?",
        "How does photosynthesis work?",
        "What is artificial intelligence?",
        "Why is the ocean salty?",
    ]

    for query in test_queries:
        print("\n" + "="*50)
        print(f"USER QUERY: {query}")
        print("="*50)
        
        result = fetch_best_wikipedia_page(query)
        
        if "error" in result:
            print(f"ERROR: {result['error']}")
        else:
            print(f"TITLE: {result['title']}")
            print(f"RELEVANCE: {result['score']:.2f}")
            print("\nCONTENT PREVIEW:")
            print("-"*50)
            # Show first 300 characters of content
            preview = result['content'][:300] + "..." if len(result['content']) > 300 else result['content']
            print(preview)
            print("-"*50)


if __name__ == "__main__":
    main()