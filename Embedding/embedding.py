"""
Embedding operations for chunking articles and storing in Pinecone.
Links chunks back to source articles using article_id metadata.
"""

import os
import re
from typing import List, Dict, Any, Optional
import pinecone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ArticleEmbedder:
    def __init__(self):
        """Initialize Pinecone client."""
        api_key = os.getenv("PINECONE_API_KEY")
        environment = os.getenv("PINECONE_ENVIRONMENT")
        index_name = os.getenv("PINECONE_INDEX_NAME")
        
        if not all([api_key, environment, index_name]):
            raise ValueError("Missing Pinecone configuration in environment")
        
        pinecone.init(api_key=api_key, environment=environment)
        self.index = pinecone.Index(index_name)
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Text to chunk
            chunk_size: Target size for each chunk (characters)
            overlap: Number of characters to overlap between chunks
            
        Returns:
            List of text chunks
        """
        if not text or len(text) <= chunk_size:
            return [text] if text else []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # If this isn't the last chunk, try to break at a sentence boundary
            if end < len(text):
                # Look for sentence endings within the last 100 characters
                search_start = max(start + chunk_size - 100, start)
                sentence_end = text.rfind('.', search_start, end)
                if sentence_end > start + chunk_size // 2:  # Only break if we find a reasonable boundary
                    end = sentence_end + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for text. This is a placeholder - you'll need to implement
        your preferred embedding method (OpenAI, sentence-transformers, etc.).
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding
        """
        # TODO: Replace with your preferred embedding method
        # Example with OpenAI:
        # import openai
        # openai.api_key = os.getenv("OPENAI_API_KEY")
        # response = openai.Embedding.create(input=text, model="text-embedding-ada-002")
        # return response['data'][0]['embedding']
        
        # Placeholder: return random embedding (replace this!)
        import numpy as np
        return np.random.rand(1536).tolist()  # OpenAI ada-002 dimension
    
    def store_article_chunks(
        self,
        article_id: str,
        text: str,
        title: Optional[str] = None,
        chunk_size: int = 1000,
        overlap: int = 200
    ) -> List[str]:
        """
        Chunk article text and store embeddings in Pinecone with article_id metadata.
        
        Args:
            article_id: The article UUID from Supabase
            text: Article text to chunk and embed
            title: Article title for metadata
            chunk_size: Target chunk size in characters
            overlap: Overlap between chunks in characters
            
        Returns:
            List of chunk IDs that were stored
        """
        chunks = self.chunk_text(text, chunk_size, overlap)
        chunk_ids = []
        
        print(f"📝 Creating {len(chunks)} chunks for article {article_id}")
        
        for i, chunk in enumerate(chunks):
            # Create unique chunk ID
            chunk_id = f"{article_id}_chunk_{i}"
            
            # Get embedding
            embedding = self.get_embedding(chunk)
            
            # Prepare metadata
            metadata = {
                "article_id": article_id,
                "chunk_index": i,
                "text": chunk,
                "title": title,
                "chunk_size": len(chunk),
                "total_chunks": len(chunks)
            }
            
            # Store in Pinecone
            try:
                self.index.upsert(
                    vectors=[{
                        "id": chunk_id,
                        "values": embedding,
                        "metadata": metadata
                    }]
                )
                chunk_ids.append(chunk_id)
                print(f"  ✅ Stored chunk {i+1}/{len(chunks)}")
            except Exception as e:
                print(f"  ❌ Error storing chunk {i}: {e}")
        
        print(f"🎯 Successfully stored {len(chunk_ids)} chunks for article {article_id}")
        return chunk_ids
    
    def search_chunks(
        self,
        query: str,
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant chunks in Pinecone.
        
        Args:
            query: Search query
            top_k: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of search results with metadata
        """
        # Get query embedding
        query_embedding = self.get_embedding(query)
        
        # Search Pinecone
        try:
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_metadata
            )
            return results.matches
        except Exception as e:
            print(f"❌ Error searching Pinecone: {e}")
            return []

# Convenience function for quick usage
def get_embedder() -> ArticleEmbedder:
    """Get a configured embedder instance."""
    return ArticleEmbedder() 