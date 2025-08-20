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
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query is required'
            }), 400
        
        print(f"🔍 Searching for: '{query}' (top_k: {top_k})")
        
        # Search Pinecone
        embedder = get_embedder()
        search_results = embedder.search_chunks(query, top_k=top_k)
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
        for article_id in article_ids:
            article = db.get_article_by_id(article_id)
            if article:
                # Add search relevance info
                best_score = scores_by_article.get(article_id, 0.0)
                article['search_relevance'] = {
                    'matching_chunks': len([h for h in hits if h['fields'].get('article_id') == article_id]),
                    'percent_match': round(best_score * 100)
                }
                articles.append(article)
        
        # Sort articles by score of max matching chunk
        articles.sort(key=lambda x: x['search_relevance']['percent_match'], reverse=True)
        
        print(f"📰 Retrieved {len(articles)} unique articles")
        
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
