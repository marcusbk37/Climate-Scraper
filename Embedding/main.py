"""
Main script demonstrating the complete workflow:
1. Store article in Supabase
2. Chunk and embed article text
3. Store embeddings in Pinecone with article_id metadata
4. Search and retrieve linked articles
"""

from database import get_db
from embedding import get_embedder

def process_article(
    url: str,
    text: str,
    title: str = None,
    authors: list = None,
    published_at: str = None,
    metadata: dict = None
):
    """
    Complete workflow: store article and create embeddings.
    
    Args:
        url: Article URL
        text: Article text content
        title: Article title
        authors: List of authors
        published_at: Publication date
        metadata: Additional metadata
    """
    print("🚀 Starting article processing workflow...")
    
    # Step 1: Store article in Supabase
    print("\n📊 Step 1: Storing article in Supabase...")
    db = get_db()
    article_id = db.store_article(
        url=url,
        text=text,
        title=title,
        authors=authors,
        published_at=published_at,
        metadata=metadata
    )
    
    # Step 2: Create embeddings and store in Pinecone
    print(f"\n🔍 Step 2: Creating embeddings for article {article_id}...")
    embedder = get_embedder()
    chunk_ids = embedder.store_article_chunks(
        article_id=article_id,
        text=text,
        title=title
    )
    
    print(f"\n✅ Workflow complete!")
    print(f"   Article ID: {article_id}")
    print(f"   Chunks created: {len(chunk_ids)}")
    return article_id, chunk_ids

def search_and_retrieve(query: str, top_k: int = 5):
    """
    Search for relevant content and retrieve source articles.
    
    Args:
        query: Search query
        top_k: Number of results to return
    """
    print(f"\n🔎 Searching for: '{query}'")
    
    # Search Pinecone
    embedder = get_embedder()
    results = embedder.search_chunks(query, top_k=top_k)
    
    if not results:
        print("❌ No results found")
        return
    
    print(f"\n📋 Found {len(results)} relevant chunks:")
    
    # Retrieve source articles
    db = get_db()
    seen_articles = set()
    
    for i, result in enumerate(results, 1):
        metadata = result.metadata
        article_id = metadata.get("article_id")
        chunk_text = metadata.get("text", "")[:200] + "..." if len(metadata.get("text", "")) > 200 else metadata.get("text", "")
        
        print(f"\n{i}. Score: {result.score:.3f}")
        print(f"   Chunk: {chunk_text}")
        print(f"   Article ID: {article_id}")
        
        # Get full article details (only once per article)
        if article_id not in seen_articles:
            article = db.get_article_by_id(article_id)
            if article:
                print(f"   📰 Source: {article.get('title', 'No title')}")
                print(f"   🌐 URL: {article.get('url', 'No URL')}")
                print(f"   📅 Published: {article.get('published_at', 'Unknown')}")
                seen_articles.add(article_id)

def demo():
    """Run a complete demonstration."""
    print("🎯 Article Storage and Embedding Demo")
    print("=" * 50)
    
    # Example article data
    sample_article = {
        "url": "https://example.com/sample-article",
        "title": "The Future of Artificial Intelligence in Healthcare",
        "text": """
        Artificial intelligence is revolutionizing healthcare in unprecedented ways. 
        From diagnostic imaging to drug discovery, AI systems are becoming increasingly 
        sophisticated and accurate. Machine learning algorithms can now detect early 
        signs of diseases like cancer with remarkable precision, often outperforming 
        human radiologists. In drug discovery, AI is accelerating the development of 
        new treatments by predicting molecular interactions and identifying promising 
        compounds. The integration of AI in electronic health records is improving 
        patient care through better data analysis and predictive modeling. However, 
        challenges remain in ensuring AI systems are transparent, unbiased, and 
        maintain patient privacy. As we move forward, the collaboration between 
        healthcare professionals and AI systems will be crucial for maximizing 
        benefits while addressing ethical concerns.
        """,
        "authors": ["Dr. Sarah Johnson", "Prof. Michael Chen"],
        "published_at": "2024-01-15T10:00:00Z",
        "metadata": {
            "category": "healthcare",
            "tags": ["AI", "healthcare", "machine learning", "diagnostics"]
        }
    }
    
    # Process the article
    article_id, chunk_ids = process_article(**sample_article)
    
    # Search for related content
    search_and_retrieve("AI healthcare diagnostics", top_k=3)
    
    print(f"\n🎉 Demo complete! Article {article_id} is now searchable in your system.")

if __name__ == "__main__":
    demo() 