# Article Storage and Embedding System

A simple system for storing articles in Supabase and creating searchable embeddings in Pinecone with stable linking between them.

## Overview

This system provides:
- **Article Storage**: Store articles in Supabase with unique UUID identifiers
- **Text Chunking**: Split articles into overlapping chunks for better search
- **Embedding Storage**: Store embeddings in Pinecone with metadata linking back to source articles
- **Search & Retrieval**: Search embeddings and retrieve full source articles

## Quick Start

### 1. Setup Environment

Copy the example environment file and fill in your API keys:

```bash
cp env_example.txt .env
```

Edit `.env` with your actual API keys:
```
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX_NAME=your_index_name
```

### 2. Create Database Schema

Run the SQL in `schema.sql` in your Supabase SQL editor:
- Go to Supabase Dashboard → SQL Editor
- Paste and run the contents of `schema.sql`

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Demo

```bash
python main.py
```

## Core Components

### Database (`database.py`)
- `ArticleDatabase`: Handles Supabase operations
- `store_article()`: Store article and return unique ID
- `get_article_by_id()`: Retrieve article by ID
- `get_articles_by_domain()`: Get articles from specific domain

### Embedding (`embedding.py`)
- `ArticleEmbedder`: Handles Pinecone operations
- `chunk_text()`: Split text into overlapping chunks
- `store_article_chunks()`: Create embeddings and store in Pinecone
- `search_chunks()`: Search for relevant content

### Main Workflow (`main.py`)
- `process_article()`: Complete workflow from storage to embedding
- `search_and_retrieve()`: Search and get source articles
- `demo()`: Example usage

## Usage Examples

### Store a Single Article

```python
from database import get_db
from embedding import get_embedder

# Store article
db = get_db()
article_id = db.store_article(
    url="https://example.com/article",
    text="Full article content here...",
    title="Article Title",
    authors=["Author Name"]
)

# Create embeddings
embedder = get_embedder()
chunk_ids = embedder.store_article_chunks(
    article_id=article_id,
    text="Full article content here...",
    title="Article Title"
)
```

### Search and Retrieve

```python
# Search for content
embedder = get_embedder()
results = embedder.search_chunks("your search query", top_k=5)

# Get source articles
db = get_db()
for result in results:
    article_id = result.metadata["article_id"]
    article = db.get_article_by_id(article_id)
    print(f"Found: {article['title']}")
```

## Key Features

### Stable Linking
- Each article gets a unique UUID in Supabase
- Pinecone chunks include `article_id` in metadata
- Direct lookup from search results to source articles

### Flexible Storage
- Store full article text in Supabase
- Optional metadata fields (authors, published date, etc.)
- JSON metadata for custom fields

### Smart Chunking
- Overlapping chunks for better context
- Sentence boundary awareness
- Configurable chunk size and overlap

## Configuration

### Chunking Parameters
- `chunk_size`: Target size in characters (default: 1000)
- `overlap`: Overlap between chunks (default: 200)

### Embedding Method
The `get_embedding()` method in `embedding.py` is a placeholder. Replace it with your preferred method:

```python
# Example with OpenAI
import openai
openai.api_key = os.getenv("OPENAI_API_KEY")
response = openai.Embedding.create(input=text, model="text-embedding-ada-002")
return response['data'][0]['embedding']

# Example with sentence-transformers
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
return model.encode(text).tolist()
```

## Database Schema

```sql
articles (
  id uuid primary key,           -- Unique identifier for linking
  url text not null,             -- Original URL
  domain text,                   -- Extracted domain
  title text,                    -- Article title
  authors jsonb,                 -- List of authors
  published_at timestamptz,      -- Publication date
  text text not null,            -- Full article text
  metadata jsonb,                -- Additional metadata
  created_at timestamptz         -- Creation timestamp
)
```

## Pinecone Metadata

Each chunk in Pinecone includes:
- `article_id`: Links back to Supabase article
- `chunk_index`: Position in original article
- `text`: The chunk text
- `title`: Article title
- `chunk_size`: Length of chunk
- `total_chunks`: Total chunks in article

## Next Steps

1. **Add URL Deduplication**: Uncomment the unique constraint in `schema.sql`
2. **Implement Real Embeddings**: Replace the placeholder in `embedding.py`
3. **Add Web Scraping**: Integrate with your existing scraper
4. **Add RLS Policies**: If using anon key instead of service role
5. **Add Batch Processing**: For processing multiple articles efficiently

## Troubleshooting

### Common Issues

1. **Missing API Keys**: Ensure all environment variables are set
2. **Pinecone Index**: Make sure your Pinecone index exists and has the right dimensions
3. **Supabase Permissions**: Use service role key for full access
4. **Embedding Dimensions**: Ensure your embedding method matches your Pinecone index dimensions

### Debug Mode

Add debug prints to see what's happening:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
``` 