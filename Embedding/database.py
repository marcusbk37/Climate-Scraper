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
            print(f"❌ Error storing article: {e}")
            raise
    
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