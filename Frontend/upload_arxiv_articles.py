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
import time
import json
import os
from pathlib import Path

# Import our existing modules
from database import ArticleDatabase
from embedding import ArticleEmbedder

def search_arxiv_with_pagination(keyword: str, max_results: int = 1000, start_index: int = 0, delay_seconds: float = 1.0) -> List[Dict[str, Any]]:
    """
    Search ArXiv for articles with pagination support and rate limiting.
    
    Args:
        keyword: Search term for ArXiv
        max_results: Maximum number of results to return
        start_index: Starting index for pagination (0-based)
        delay_seconds: Delay between API calls to respect rate limits
        
    Returns:
        List of article dictionaries with title, abstract, authors, etc.
    """
    all_articles = []
    current_start = start_index
    batch_size = 100  # ArXiv API maximum per request
    
    print(f"🔍 Searching ArXiv for articles about '{keyword}'...")
    print(f"📊 Target: {max_results} articles, starting from index {start_index}")
    
    while len(all_articles) < max_results:
        # Calculate how many results to request in this batch
        remaining = max_results - len(all_articles)
        current_batch_size = min(batch_size, remaining)
        
        print(f"\n📡 Fetching batch: {len(all_articles) + 1} to {len(all_articles) + current_batch_size} (starting from index {current_start})")
        
        # URL encode the keyword for the query
        encoded_keyword = urllib.parse.quote(keyword)
        
        # Construct the ArXiv API query URL with pagination
        query_url = f'http://export.arxiv.org/api/query?search_query=all:{encoded_keyword}&start={current_start}&max_results={current_batch_size}'
        
        try:
            # Add delay to respect rate limits
            if current_start > start_index:  # Don't delay on first request
                print(f"⏳ Waiting {delay_seconds} seconds to respect rate limits...")
                time.sleep(delay_seconds)
            
            # Make the request
            response = urllib.request.urlopen(query_url)
            data = response.read().decode('utf-8')
            
            # Parse XML response
            root = ET.fromstring(data)
            
            # Check if we got any results
            entries = root.findall('.//{http://www.w3.org/2005/Atom}entry')
            if not entries:
                print("📭 No more results found - reached end of available articles")
                break
            
            print(f"✅ Found {len(entries)} articles in this batch")
            
            # Extract articles from this batch
            batch_articles = []
            for entry in entries:
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
                
                batch_articles.append(article)
            
            all_articles.extend(batch_articles)
            
            # Move to next batch
            current_start += len(entries)
            
            # If we got fewer results than requested, we've reached the end
            if len(entries) < current_batch_size:
                print("📭 Reached end of available results")
                break
                
        except Exception as e:
            print(f"❌ Error occurred while searching ArXiv batch starting at {current_start}: {e}")
            print("🔄 Continuing with next batch...")
            current_start += current_batch_size
            continue
    
    print(f"\n🎯 Search complete! Found {len(all_articles)} articles total")
    return all_articles

def save_progress(keyword: str, processed_count: int, total_count: int, failed_articles: List[str], progress_file: str = "arxiv_upload_progress.json"):
    """
    Save upload progress to allow resuming later.
    
    Args:
        keyword: The search keyword used
        processed_count: Number of articles successfully processed
        total_count: Total number of articles found
        failed_articles: List of article URLs that failed to process
        progress_file: File to save progress to
    """
    progress_data = {
        "keyword": keyword,
        "processed_count": processed_count,
        "total_count": total_count,
        "failed_articles": failed_articles,
        "last_updated": datetime.now().isoformat(),
        "status": "in_progress" if processed_count < total_count else "completed"
    }
    
    try:
        with open(progress_file, 'w') as f:
            json.dump(progress_data, f, indent=2)
        print(f"💾 Progress saved: {processed_count}/{total_count} articles processed")
    except Exception as e:
        print(f"❌ Error saving progress: {e}")

def load_progress(progress_file: str = "arxiv_upload_progress.json") -> Optional[Dict[str, Any]]:
    """
    Load previous upload progress to resume from where we left off.
    
    Args:
        progress_file: File to load progress from
        
    Returns:
        Progress data dictionary or None if no progress file exists
    """
    try:
        if os.path.exists(progress_file):
            with open(progress_file, 'r') as f:
                progress_data = json.load(f)
            print(f"📂 Found progress file: {progress_data['processed_count']}/{progress_data['total_count']} articles processed")
            return progress_data
        else:
            print("📂 No progress file found - starting fresh")
            return None
    except Exception as e:
        print(f"❌ Error loading progress: {e}")
        return None

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

def upload_arxiv_articles_with_resume(
    keyword: str = "quantum computing", 
    max_results: int = 1000,
    delay_seconds: float = 1.0,
    progress_file: str = "arxiv_upload_progress.json",
    resume: bool = True
):
    """
    Main function to search ArXiv and upload articles with resume capability.
    
    Args:
        keyword: Search term for ArXiv
        max_results: Maximum number of articles to process
        delay_seconds: Delay between API calls
        progress_file: File to save/load progress
        resume: Whether to resume from previous progress
    """
    print(f"🚀 Starting ArXiv article upload process...")
    
    # Check for existing progress
    progress_data = None
    if resume:
        progress_data = load_progress(progress_file)
    
    # Initialize database and embedder
    try:
        db = ArticleDatabase()
        embedder = ArticleEmbedder()
        print("✅ Successfully initialized database and embedder")
    except Exception as e:
        print(f"❌ Error initializing database or embedder: {e}")
        return
    
    # If resuming, check if we need to search again
    if progress_data and progress_data['status'] == 'completed':
        print("✅ Previous upload was completed successfully!")
        return
    
    # Search ArXiv (only if not resuming or if we need more articles)
    if not progress_data or progress_data['processed_count'] < progress_data['total_count']:
        # If resuming, we might need to search again to get the full list
        # For simplicity, we'll search again and rely on duplicate detection
        print(f"🔍 Searching ArXiv for articles about '{keyword}'...")
        articles = search_arxiv_with_pagination(keyword, max_results, delay_seconds=delay_seconds)
        
        if not articles:
            print("❌ No articles found or error occurred during search")
            return
    else:
        # We have progress data and all articles were found
        articles = []  # We'll rely on the progress data
    
    # Track progress
    processed_count = progress_data['processed_count'] if progress_data else 0
    failed_articles = progress_data.get('failed_articles', []) if progress_data else []
    total_count = len(articles) if articles else (progress_data['total_count'] if progress_data else 0)
    
    print(f"📊 Processing {total_count} articles (starting from {processed_count})")
    
    # Process each article
    successful_uploads = 0
    skipped_duplicates = 0
    
    for i, article in enumerate(articles[processed_count:], processed_count + 1):
        print(f"\n📄 Processing article {i}/{total_count}: {article.get('title', 'Unknown Title')}")
        
        try:
            # Prepare article data
            url = article.get('url', '')
            title = article.get('title', '')
            authors = article.get('authors', [])
            published_at = article.get('published_at', '')
            arxiv_id = article.get('arxiv_id', '')
            
            # Note: Deduplication is handled by database unique constraint on URL
            # The store_article method will return existing article ID if URL already exists
            
            # Combine title and abstract for the full text
            abstract = article.get('abstract', '')
            full_text = f"Title: {title}\n\nAbstract: {abstract}"
            full_text = clean_text_for_embedding(full_text)
            
            # Prepare metadata
            metadata = {
                'type': 'research_paper',
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
                failed_articles.append(url)
                processed_count += 1
                save_progress(keyword, processed_count, total_count, failed_articles, progress_file)
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
                failed_articles.append(url)
            
            # Update progress
            processed_count += 1
            save_progress(keyword, processed_count, total_count, failed_articles, progress_file)
                
        except Exception as e:
            print(f"  ❌ Error processing article: {e}")
            failed_articles.append(article.get('url', 'unknown'))
            processed_count += 1
            save_progress(keyword, processed_count, total_count, failed_articles, progress_file)
            continue
    
    # Mark as completed
    save_progress(keyword, processed_count, total_count, failed_articles, progress_file)
    
    print(f"\n🎯 Upload complete!")
    print(f"📊 Successfully processed: {successful_uploads} articles")
    print(f"⏭️  Skipped duplicates: {skipped_duplicates} articles")
    print(f"❌ Failed articles: {len(failed_articles)} articles")
    print(f"📈 Total articles processed: {processed_count} articles")
    print(f"💾 Articles stored in Supabase and embeddings uploaded to Pinecone")
    
    if failed_articles:
        print(f"\n📋 Failed articles URLs:")
        for url in failed_articles:
            print(f"  - {url}")

# Keep the original function for backward compatibility
def search_arxiv(keyword: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Original search function for backward compatibility.
    """
    return search_arxiv_with_pagination(keyword, max_results, 0, 1.0)

def upload_arxiv_articles(keyword: str = "quantum computing", max_results: int = 5):
    """
    Original upload function for backward compatibility.
    """
    upload_arxiv_articles_with_resume(keyword, max_results, 1.0, "arxiv_upload_progress.json", False)

def test_arxiv_deduplication():
    """Test that ArXiv article deduplication works correctly."""
    db = ArticleDatabase()
    article_id_1 = db.store_article(url="https://arxiv.org/abs/2401.00123", text="Test content", title="Test Title")
    article_id_2 = db.store_article(url="https://arxiv.org/abs/2401.00123", text="Different content", title="Different Title") 
    print("✅ Found duplicate" if article_id_1 == article_id_2 else "❌ Created duplicate article")


def main():
    """Main function to run the upload process."""
    print("🚀 Starting ArXiv article upload process...")
    
    # You can modify these parameters
    keyword = "climate AI"  # Change this to search for different topics
    max_results = 1000  # Number of articles to process
    delay_seconds = 1.0  # Delay between API calls
    
    # Uncomment the line below to test de-duplication
    test_arxiv_deduplication()
    
    # Use the new paginated search function
    # search_arxiv_with_pagination(keyword, max_results, 0, delay_seconds)
    
    # Use the new upload function with resume capability
    # upload_arxiv_articles_with_resume(keyword, max_results, delay_seconds, resume=True)

if __name__ == "__main__":
    main()
