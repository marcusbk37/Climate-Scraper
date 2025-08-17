from flask import Flask, render_template, request, jsonify
import sys
import os
from datetime import datetime

# Add the Embedding directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Embedding'))

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
        
        # Extract unique article IDs
        article_ids = set()
        for hit in hits:
            article_id = hit['fields'].get('article_id')
            if article_id:
                article_ids.add(article_id)
        
        # Retrieve full article details from Supabase
        db = get_db()
        articles = []
        for article_id in article_ids:
            article = db.get_article_by_id(article_id)
            if article:
                # Add search relevance info
                article['search_relevance'] = {
                    'matching_chunks': len([h for h in hits if h['fields'].get('article_id') == article_id])
                }
                articles.append(article)
        
        # Sort articles by number of matching chunks
        articles.sort(key=lambda x: x['search_relevance']['matching_chunks'], reverse=True)
        
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
