from flask import Flask, render_template, request, jsonify
import sys
import os
from datetime import datetime

# Import local modules
from database import get_db
from embedding import get_embedder

app = Flask(__name__)

@app.route('/')
def index():
    """Main search page."""
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    """Handle search requests."""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        top_k = data.get('top_k', 10)
        content_type = data.get('content_type', '').strip()
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query is required'
            }), 400
        
        print(f"🔍 Searching for: '{query}' (top_k: {top_k})")
        
        # Search Pinecone
        embedder = get_embedder()
        # If filtering by content type, search for more results to ensure we get enough of the desired type
        search_top_k = top_k * 3 if content_type else top_k  # Get 3x more results when filtering
        search_results = embedder.search_chunks(query, top_k=search_top_k)
        print("hello")
        
        if not search_results or not search_results.get('result', {}).get('hits'):
            return jsonify({
                'success': True,
                'query': query,
                'total_hits': 0,
                'unique_articles': 0,
                'articles': [],
                'message': 'No relevant articles found for your search query.'
            })
        
        hits = search_results['result']['hits']
        print(f"✅ Found {len(hits)} relevant chunks")
        for hit in hits:
            print(hit["_score"]) # this is how you access the similarity score. good.
        
        # Extract unique article IDs and track best scores
        article_ids = set()
        scores_by_article = {} # dictionary to track best-scoring chunk for each article
        for hit in hits:
            article_id = hit['fields'].get('article_id')
            if article_id:
                article_ids.add(article_id)
                # Track the best score for each article
                current_best = scores_by_article.get(article_id, 0.0)
                scores_by_article[article_id] = max(current_best, hit['_score'])
        
        # Retrieve full article details from Supabase
        db = get_db()
        articles = []
        
        # Calculate relative scoring based on top result
        top_score = max(scores_by_article.values()) if scores_by_article else 1.0
        
        for article_id in article_ids:
            article = db.get_article_by_id(article_id)
            if article:
                # Apply content type filter if specified
                if content_type:
                    article_type = article.get('metadata', {}).get('type', '').lower()
                    if article_type != content_type.lower():
                        continue
                
                # Add search relevance info
                best_score = scores_by_article.get(article_id, 0.0)
                absolute_percent = (90 if 1.5 * best_score * 100 > 90 else round(best_score * 100 * 1.5))
                relative_percent = round((best_score / top_score) * 100) if top_score > 0 else 0
                
                article['search_relevance'] = {
                    'matching_chunks': len([h for h in hits if h['fields'].get('article_id') == article_id]),
                    'percent_match': ("90+" if absolute_percent == 90 else str(absolute_percent)),
                    'relative_relevance': relative_percent
                }
                articles.append(article)
        
        # Sort articles by score of max matching chunk
        articles.sort(key=lambda x: x['search_relevance']['percent_match'], reverse=True)
        
        # Limit to requested number of results
        articles = articles[:top_k]
        
        print(f"📰 Retrieved {len(articles)} unique articles (filtered from {len(article_ids)} candidates)")
        
        return jsonify({
            'success': True,
            'query': query,
            'total_hits': len(hits),
            'unique_articles': len(articles),
            'articles': articles,
            'search_timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Search error: {e}")
        return jsonify({
            'success': False,
            'error': f'Search failed: {str(e)}'
        }), 500

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
