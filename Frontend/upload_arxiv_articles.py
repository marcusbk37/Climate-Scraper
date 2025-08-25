"""
Script to search ArXiv for articles and upload them to both Supabase and Pinecone.
Uses the existing database.py and embedding.py modules from the Frontend folder.
"""

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

# Import our existing modules
from database import ArticleDatabase
from embedding import ArticleEmbedder

def search_arxiv(keyword: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Search ArXiv for articles and return structured data.
    
    Args:
        keyword: Search term for ArXiv
        max_results: Maximum number of results to return
        
    Returns:
        List of article dictionaries with title, abstract, authors, etc.
    """
    # URL encode the keyword for the query
    encoded_keyword = urllib.parse.quote(keyword)
    
    # Construct the ArXiv API query URL
    query_url = f'http://export.arxiv.org/api/query?search_query=all:{encoded_keyword}&start=0&max_results={max_results}'
    
    try:
        # Make the request
        response = urllib.request.urlopen(query_url)
        data = response.read().decode('utf-8')
        
        # Parse XML response
        root = ET.fromstring(data)
        
        # Extract articles
        articles = []
        for entry in root.findall('.//{http://www.w3.org/2005/Atom}entry'):
            article = {}
            
            # Extract title
            title_elem = entry.find('.//{http://www.w3.org/2005/Atom}title')
            if title_elem is not None:
                article['title'] = title_elem.text.strip()
            
            # Extract abstract
            summary_elem = entry.find('.//{http://www.w3.org/2005/Atom}summary')
            if summary_elem is not None:
                article['abstract'] = summary_elem.text.strip()
            
            # Extract authors
            authors = []
            for author_elem in entry.findall('.//{http://www.w3.org/2005/Atom}author/{http://www.w3.org/2005/Atom}name'):
                if author_elem.text:
                    authors.append(author_elem.text.strip())
            article['authors'] = authors
            
            # Extract publication date
            published_elem = entry.find('.//{http://www.w3.org/2005/Atom}published')
            if published_elem is not None:
                article['published_at'] = published_elem.text.strip()
            
            # Extract ArXiv ID and URL
            id_elem = entry.find('.//{http://www.w3.org/2005/Atom}id')
            if id_elem is not None:
                article['arxiv_id'] = id_elem.text.strip()
                # Convert ArXiv ID to URL
                article['url'] = f"https://arxiv.org/abs/{article['arxiv_id'].split('/')[-1]}"
            
            # Extract categories
            categories = []
            for category_elem in entry.findall('.//{http://arxiv.org/schemas/atom}primary_category'):
                if category_elem.get('term'):
                    categories.append(category_elem.get('term'))
            for category_elem in entry.findall('.//{http://arxiv.org/schemas/atom}category'):
                if category_elem.get('term'):
                    categories.append(category_elem.get('term'))
            article['categories'] = list(set(categories))  # Remove duplicates
            
            articles.append(article)
        
        print(f"\nFound {len(articles)} papers related to '{keyword}':\n")
        for i, article in enumerate(articles, 1):
            print(f"Paper {i}:")
            print(f"Title: {article.get('title', 'N/A')}")
            print(f"Authors: {', '.join(article.get('authors', []))}")
            print(f"URL: {article.get('url', 'N/A')}")
            print(f"Categories: {', '.join(article.get('categories', []))}")
            print(f"Abstract: {article.get('abstract', 'N/A')}")
            print("-" * 80)
        
        return articles
        
    except Exception as e:
        print(f"Error occurred while searching ArXiv: {e}")
        return []

def clean_text_for_embedding(text: str) -> str:
    """
    Clean text for better embedding quality.
    
    Args:
        text: Raw text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters that might interfere with embeddings
    text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]]', '', text)
    print(text)

    return text.strip()

def upload_arxiv_articles(keyword: str = "quantum computing", max_results: int = 5):
    """
    Main function to search ArXiv and upload articles to Supabase and Pinecone.
    
    Args:
        keyword: Search term for ArXiv
        max_results: Maximum number of articles to process
    """
    print(f"🔍 Searching ArXiv for articles about '{keyword}'...")
    
    # Search ArXiv
    articles = search_arxiv(keyword, max_results)
    
    if not articles:
        print("❌ No articles found or error occurred during search")
        return
    
    # Initialize database and embedder
    try:
        db = ArticleDatabase()
        embedder = ArticleEmbedder()
        print("✅ Successfully initialized database and embedder")
    except Exception as e:
        print(f"❌ Error initializing database or embedder: {e}")
        return
    
    # Process each article
    successful_uploads = 0
    
    for i, article in enumerate(articles, 1):
        print(f"\n📄 Processing article {i}/{len(articles)}: {article.get('title', 'Unknown Title')}")
        
        try:
            # Prepare article data
            url = article.get('url', '')
            title = article.get('title', '')
            authors = article.get('authors', [])
            published_at = article.get('published_at', '')
            
            # Combine title and abstract for the full text
            abstract = article.get('abstract', '')
            full_text = f"Title: {title}\n\nAbstract: {abstract}"
            full_text = clean_text_for_embedding(full_text)
            
            # Prepare metadata
            metadata = {
                'arxiv_id': article.get('arxiv_id', ''),
                'categories': article.get('categories', []),
                'source': 'arxiv',
                'search_keyword': keyword
            }
            
            # Store in Supabase
            print(f"  💾 Storing in Supabase...")
            article_id = db.store_article(
                url=url,
                text=full_text,
                title=title,
                authors=authors,
                published_at=published_at,
                metadata=metadata
            )
            
            if not article_id:
                print(f"  ❌ Failed to store article in Supabase")
                continue
            
            # Store embeddings in Pinecone
            print(f"  🧠 Storing embeddings in Pinecone...")
            chunk_ids = embedder.store_article_chunks(
                article_id=article_id,
                text=full_text,
                title=title
            )
            
            if chunk_ids:
                print(f"  ✅ Successfully uploaded article with {len(chunk_ids)} chunks")
                successful_uploads += 1
            else:
                print(f"  ❌ Failed to store embeddings in Pinecone")
                
        except Exception as e:
            print(f"  ❌ Error processing article: {e}")
            continue
    
    print(f"\n🎯 Upload complete! Successfully processed {successful_uploads}/{len(articles)} articles")
    print(f"📊 Articles stored in Supabase and embeddings uploaded to Pinecone")

def main():
    """Main function to run the upload process."""
    print("🚀 Starting ArXiv article upload process...")
    
    # You can modify these parameters
    keyword = "climate AI"  # Change this to search for different topics
    max_results = 5  # Number of articles to process
    
    search_arxiv(keyword)
    # upload_arxiv_articles(keyword, max_results)

if __name__ == "__main__":
    main()
