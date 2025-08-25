"""
Database operations for article storage using Supabase.
Handles storing articles and retrieving them by ID for Pinecone linking.
"""

import os
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ArticleDatabase:
    def __init__(self):
        """Initialize Supabase client."""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in environment")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
    
    def store_article(
        self,
        url: str,
        text: str,
        title: Optional[str] = None,
        authors: Optional[List[str]] = None,
        published_at: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store an article and return its unique ID for Pinecone linking.
        
        Args:
            url: The article URL
            text: The full article text content
            title: Article title (optional)
            authors: List of author names (optional)
            published_at: Publication date in ISO format (optional)
            metadata: Additional metadata as dict (optional)
            
        Returns:
            str: The article ID (UUID) to use in Pinecone metadata
        """
        domain = urlparse(url).hostname
        
        payload = {
            "url": url,
            "domain": domain,
            "title": title,
            "authors": authors or [],
            "published_at": published_at,
            "text": text,
            "metadata": metadata or {}
        }
        
        try:
            result = self.supabase.table("articles").insert(payload).execute()
            article_id = result.data[0]["id"]
            print(f"✅ Stored article: {title or url} (ID: {article_id})")
            return article_id
        except Exception as e:
            # Handle duplicate key violation
            if "duplicate key value violates unique constraint" in str(e).lower():
                # Get the existing article ID
                try:
                    result = self.supabase.table("articles").select("id").eq("url", url).single().execute()
                    existing_id = result.data["id"]
                    print(f"⏭️  Article already exists: {title or url} (ID: {existing_id})")
                    return existing_id
                except Exception as get_error:
                    print(f"❌ Error retrieving existing article: {get_error}")
                    raise
            else:
                print(f"❌ Error storing article: {e}")
                raise
    
    # this should work with research papers too
    def get_article_by_id(self, article_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an article by its ID.
        
        Args:
            article_id: The article UUID
            
        Returns:
            Dict with article data or None if not found
        """
        try:
            result = self.supabase.table("articles").select("*").eq("id", article_id).single().execute()
            return result.data
            # or would I rather return just the text? rn, leaving it as returning the article
        except Exception as e:
            print(f"❌ Error retrieving article {article_id}: {e}")
            return None
    
    def get_articles_by_domain(self, domain: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get articles from a specific domain.
        
        Args:
            domain: Domain name (e.g., 'example.com')
            limit: Maximum number of articles to return
            
        Returns:
            List of article dictionaries
        """
        try:
            result = self.supabase.table("articles").select("*").eq("domain", domain).limit(limit).execute()
            return result.data
        except Exception as e:
            print(f"❌ Error retrieving articles for domain {domain}: {e}")
            return []
    
    def get_recent_articles(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recently created articles.
        
        Args:
            limit: Maximum number of articles to return
            
        Returns:
            List of article dictionaries
        """
        try:
            result = self.supabase.table("articles").select("*").order("created_at", desc=True).limit(limit).execute()
            return result.data
        except Exception as e:
            print(f"❌ Error retrieving recent articles: {e}")
            return []
    

# Convenience function for quick usage
def get_db() -> ArticleDatabase:
    """Get a configured database instance."""
    return ArticleDatabase()

def test_store_article():
    """Test storing articles in the database."""
    db = ArticleDatabase()
    
    print("\nTesting article storage...")
    
    # Test storing basic article
    test_article = {
        "url": "https://example.com/test",
        "domain": "example.com",
        "title": "Test Article", 
        "text": "This is a test article.",
        "authors": ["Test Author"],
        "published_at": "2023-01-01T00:00:00Z"
    }
    
    print("\nTrying to store basic article...")
    article_id = db.store_article(test_article["url"], test_article["text"], test_article["title"], test_article["authors"], test_article["published_at"])
    if article_id is not None:
        print(f"✅ Successfully stored article with ID: {article_id}")
    else:
        print("❌ Failed to store article")
    assert article_id is not None, "Article storage failed"
    
    # Test storing article with missing optional fields
    minimal_article = {
        "url": "https://example.com/minimal",
        "text": "Minimal test article."
    }
    
    print("\nTrying to store minimal article...")
    minimal_id = db.store_article(minimal_article["url"], minimal_article["text"])
    if minimal_id is not None:
        print(f"✅ Successfully stored minimal article with ID: {minimal_id}")
    else:
        print("❌ Failed to store minimal article")
    assert minimal_id is not None, "Minimal article storage failed"

    print("\n🎯 All article storage tests completed")

def test_get_article_by_id():
    """Test retrieving an article by its ID."""
    db = ArticleDatabase()
    article_id = "49659337-1873-47dd-9586-a357e7f72b74"
    article = db.get_article_by_id(article_id)
    print(f"Article: {article}")

def test_get_articles_by_domain():
    """Test retrieving articles by domain."""
    db = ArticleDatabase()
    domain = "example.com"
    articles = db.get_articles_by_domain(domain)
    print(f"Articles: {articles}")

def test_get_recent_articles():
    """Test retrieving recent articles."""
    db = ArticleDatabase()
    articles = db.get_recent_articles()
    print(f"Articles: {articles}")

if __name__ == "__main__":
    # test_store_article()
    # test_get_article_by_id()
    # test_get_articles_by_domain()
    test_get_recent_articles()