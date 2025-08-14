"""
Single Article Pipeline
Complete workflow for processing a single article:
1. Upload a new article to Supabase
2. Get the full article from Supabase
3. Chunk + upload that article to pinecone
4. Search pinecone and retrieve results
"""

import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from dotenv import load_dotenv

from database import get_db, ArticleDatabase
from embedding import get_embedder, ArticleEmbedder

# Load environment variables
load_dotenv()

class SingleArticlePipeline:
    def __init__(self):
        """Initialize the pipeline with database and embedder instances."""
        self.db = get_db()
        self.embedder = get_embedder()

    def run_complete_pipeline(
        self,
        url: str,
        text: str,
        title: Optional[str] = None,
        authors: Optional[List[str]] = None,
        published_at: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        search_query: str = None,
        chunk_size: int = 1000,
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        Run the complete pipeline for a single article.
        
        Args:
            url: Article URL (required)
            text: Article text content (required)
            title: Article title (optional)
            authors: List of authors (optional)
            published_at: Publication date (optional)
            metadata: Additional metadata (optional)
            search_query: Query to search for after processing (optional)
            chunk_size: Size of text chunks
            top_k: Number of search results to return
        
        Returns:
            Dictionary with complete pipeline results
        """
        print("🎯 Single Article Pipeline")
        print("=" * 50)
        print(f"Processing article: {title or url}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("=" * 50)
        
        pipeline_results = {
            'timestamp': datetime.now().isoformat(),
            'article_info': {
                'url': url,
                'title': title,
                'text_length': len(text)
            },
            'step1_upload': {},
            'step2_retrieve': {},
            'step3_chunk_upload': {},
            'step4_search': {},
            'summary': {}
        }
        
        try:
            # Step 1: Upload to Supabase
            print("\n📤 STEP 1: Uploading article to Supabase")
            print("-" * 40)
            article_id = self.db.store_article(
                url=url,
                text=text,
                title=title,
                authors=authors,
                published_at=published_at,
                metadata=metadata
            )
            print(f"✅ Successfully uploaded article to Supabase")
            print(f"   Article ID: {article_id}")
            print(f"   Title: {title or 'Untitled'}")
            print(f"   URL: {url}")
            pipeline_results['step1_upload'] = {
                'success': True,
                'article_id': article_id
            }
            
            # Step 2: Get from Supabase
            print(f"\n📥 STEP 2: Retrieving article from Supabase")
            print("-" * 40)
            article = self.db.get_article_by_id(article_id)
            if not article:
                raise Exception("Failed to retrieve article from Supabase")
            
            print(f"✅ Successfully retrieved article from Supabase")
            print(f"   Article ID: {article['id']}")
            print(f"   Title: {article.get('title', 'Untitled')}")
            print(f"   URL: {article.get('url', 'No URL')}")
            print(f"   Text length: {len(article.get('text', ''))} characters")
            
            pipeline_results['step2_retrieve'] = {
                'success': True,
                'article': {
                    'id': article['id'],
                    'title': article.get('title'),
                    'url': article.get('url'),
                    'text_length': len(article.get('text', ''))
                }
            }
            
            # Step 3: Chunk and upload to Pinecone
            print(f"\n🔍 STEP 3: Chunking and uploading to Pinecone")
            print("-" * 40)
            print(f"Processing article: {title or 'Untitled'}")
            print(f"Text length: {len(text)} characters")
            print(f"Chunk size: {chunk_size} characters")
            
            chunk_ids = self.embedder.store_article_chunks(
                article_id=article_id,
                text=article['text'],
                title=article.get('title'),
                chunk_size=chunk_size
            )
            print(f"✅ Successfully uploaded {len(chunk_ids)} chunks to Pinecone")
            
            pipeline_results['step3_chunk_upload'] = {
                'success': True,
                'chunk_count': len(chunk_ids),
                'chunk_ids': chunk_ids
            }
            
            # Step 4: Search Pinecone (if query provided)
            if search_query:
                print(f"\n🔎 STEP 4: Searching Pinecone")
                print("-" * 40)
                print(f"Searching for: '{search_query}'")
                print(f"Top-k: {top_k}")
                
                search_results = self.embedder.search_chunks(search_query, top_k=top_k)
                
                if not search_results or not search_results.get('result', {}).get('hits'):
                    print("❌ No search results found")
                    pipeline_results['step4_search'] = {
                        'success': True,
                        'search_query': search_query,
                        'total_hits': 0,
                        'unique_articles': 0,
                        'results': {'results': [], 'articles': [], 'total_hits': 0}
                    }
                else:
                    hits = search_results['result']['hits']
                    print(f"✅ Found {len(hits)} relevant chunks")
                    
                    # Extract unique article IDs and retrieve full articles
                    article_ids = set()
                    
                    for hit in hits:
                        article_id = hit['fields']['article_id']
                        
                        if article_id:
                            article_ids.add(article_id)
                    
                    print(f"article_ids: {article_ids}")

                    # Retrieve full article details
                    articles = []
                    for article_id in article_ids:
                        article = self.db.get_article_by_id(article_id)
                        if article:
                            articles.append(article)
                    
                    print(f"📰 Retrieved {len(articles)} unique articles")
                    
                    pipeline_results['step4_search'] = {
                        'success': True,
                        'search_query': search_query,
                        'total_hits': len(hits),
                        'unique_articles': len(articles),
                        'articles': articles
                    }
            else:
                pipeline_results['step4_search'] = {
                    'success': False,
                    'reason': 'No search query provided'
                }
            
            # Generate summary
            pipeline_results['summary'] = {
                'pipeline_success': True,
                'article_processed': True,
                'chunks_created': len(chunk_ids),
                'search_performed': search_query is not None
            }
            
            print("\n🎉 Pipeline Complete!")
            print("=" * 50)
            print(f"📊 Summary:")
            print(f"   ✅ Article uploaded to Supabase: {article_id}")
            print(f"   📄 Chunks created in Pinecone: {len(chunk_ids)}")
            if search_query:
                print(f"   🔍 Search performed: '{search_query}'")
                print(f"   📰 Search results: {pipeline_results['step4_search']['total_hits']} hits")
            
            return pipeline_results
            
        except Exception as e:
            print(f"\n❌ Pipeline failed: {e}")
            pipeline_results['summary'] = {
                'pipeline_success': False,
                'error': str(e)
            }
            return pipeline_results

def demo_single_article():
    """Run a demonstration of the single article pipeline."""
    
    # Sample article data
    sample_article = {
        "url": "https://example.com/ai-healthcare-2024",
        "title": "AI Revolution in Healthcare: 2024 Update",
        "text": """
        Artificial intelligence is transforming healthcare delivery across the globe in unprecedented ways. 
        From diagnostic imaging to personalized treatment plans, AI systems are becoming essential tools 
        for medical professionals. Machine learning algorithms can now detect early signs of diseases 
        with remarkable accuracy, often outperforming human experts in specific diagnostic tasks.
        
        In drug discovery, AI is accelerating the development of new treatments by predicting molecular 
        interactions and identifying promising compounds. The integration of AI in electronic health 
        records is improving patient care through better data analysis and predictive modeling. 
        However, challenges remain in ensuring AI systems are transparent, unbiased, and maintain 
        patient privacy. As we move forward, the collaboration between healthcare professionals 
        and AI systems will be crucial for maximizing benefits while addressing ethical concerns.
        
        Recent developments in natural language processing have enabled AI systems to better understand 
        and process medical literature, patient records, and clinical notes. This capability is 
        revolutionizing how medical professionals access and utilize information for patient care.
        """,
        "authors": ["Dr. Sarah Johnson", "Prof. Michael Chen"],
        "published_at": "2024-01-25T10:00:00Z",
        "metadata": {
            "category": "healthcare",
            "tags": ["AI", "healthcare", "machine learning", "diagnostics", "2024"]
        }
    }
    
    # Initialize pipeline
    pipeline = SingleArticlePipeline()
    
    # Run complete pipeline
    results = pipeline.run_complete_pipeline(
        url=sample_article["url"],
        text=sample_article["text"],
        title=sample_article["title"],
        authors=sample_article["authors"],
        published_at=sample_article["published_at"],
        metadata=sample_article["metadata"],
        search_query="AI healthcare diagnostics machine learning",
        chunk_size=1000,
        top_k=5
    )
    
    # Display search results if available
    if results['step4_search'].get('success') and results['step4_search'].get('articles'):
        print("\n📋 Search Results:")
        print("-" * 30)
        search_results = results['step4_search']['articles']
        
        for i, result in enumerate(search_results[:3], 1):
            print(f"\n{i}. Title: {result['title']}")
            print(f"   Chunk: {result['text'][:150]}...")
            print(f"   Article ID: {result['id']}")
    
    print(f"results: {results}")
    return results

if __name__ == "__main__":
    demo_single_article()
