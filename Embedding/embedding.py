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
        
        pc = pinecone.Pinecone(api_key=api_key)
        self.index = pc.Index(index_name)
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 0) -> List[str]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Text to chunk
            chunk_size: Target size for each chunk (characters)
            overlap: Number of characters to overlap between chunks (default to 0 - was having problems with small chunks)
            
        Returns:
            List of text chunks
        """
        if not text or len(text) <= chunk_size:
            return [text] if text else []
        
        chunks = []
        start = 0
        
        while start < len(text):
            # Calculate the end position for this chunk
            end = start + chunk_size
            
            # If we haven't reached the end of the text yet
            if end < len(text):
                # Calculate where to start searching for a sentence boundary
                # We want to look in the last 100 characters of the chunk,
                # but never before the chunk's start position.
                # For example, if chunk_size is 1000:
                # - Normally search from position 900 (1000-100) to 1000
                # - But if start position is 950, search from 950 to 1000 instead
                search_start = max(start + chunk_size - 100, start)

                # Add a small buffer to check for sentence endings just after chunk end
                # Only check buffer if no period found in main window
                print("period found: ", text.rfind('.', chunk_size // 2, end))
                if text.rfind('.', chunk_size // 2, end) == -1:
                    print("hi2")
                    buffer_end = min(end + 20, len(text))
                    print(buffer_end)

                    # Find sentence end in buffer, see if it is close enough to the chunk end
                    buffer_sentence_end = text.find('.', end, buffer_end)
                    if buffer_sentence_end != -1 and buffer_sentence_end - end < 20:
                        end = buffer_sentence_end + 1
                
                # Find last period in the search window
                sentence_end = text.rfind('.', search_start, end)
                
                # Only use sentence boundary if it's not too early in chunk
                # This prevents tiny chunks
                if sentence_end > start + chunk_size // 2:
                    end = sentence_end + 1
            else:
                # If we're past text length, cap at text length
                end = len(text)
            
            # Extract the chunk and clean whitespace
            chunk = text[start:end].strip()
            
            # Only add non-empty chunks
            if chunk:
                chunks.append(chunk)
            
            # Move start position forward by chunk size minus overlap
            # This creates overlapping chunks
            start = end - overlap
            
        return chunks
    
    def store_article_chunks(
        self,
        article_id: str,
        text: str, # passes in the entire article. chunks within the function.
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
                self.index.upsert_records("ns1", [{
                    "_id": chunk_id,
                    "text": chunk,
                    "article_id": article_id,
                    "chunk_index": i,
                    "title": title,
                    "chunk_size": len(chunk),
                    "total_chunks": len(chunks)
                }])
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

def test_chunk_text():
    """Test the text chunking functionality."""
    # Test basic chunking
    print("\nTesting basic chunking...")
    text = "This is a test. Another sentence here. And one more."
    chunks = ArticleEmbedder().chunk_text(text, chunk_size=20)
    for chunk in chunks:
        print(chunk)
    assert len(chunks) == 3
    assert chunks[0] == "This is a test."
    assert chunks[1] == "Another sentence here."
    assert chunks[2] == "And one more."
    print("✅ Basic chunking test passed")

    # Test empty text
    print("\nTesting empty text...")
    chunks = ArticleEmbedder().chunk_text("", chunk_size=100)
    assert len(chunks) == 0
    print("✅ Empty text test passed")

    # Test text shorter than chunk size
    print("\nTesting text shorter than chunk size...")
    short_text = "Short text."
    chunks = ArticleEmbedder().chunk_text(short_text, chunk_size=100)
    assert len(chunks) == 1
    assert chunks[0] == short_text
    print("✅ Short text test passed")

    # Test with different chunk sizes
    print("\nTesting different chunk sizes...")
    long_text = "First sentence. Second sentence. Third sentence. Fourth sentence."
    chunks_small = ArticleEmbedder().chunk_text(long_text, chunk_size=20)
    chunks_large = ArticleEmbedder().chunk_text(long_text, chunk_size=50)
    assert len(chunks_small) > len(chunks_large)
    print("✅ Different chunk sizes test passed")

    # Test preservation of sentence boundaries
    print("\nTesting sentence boundary preservation...")
    text_with_periods = "Sentence one. Sentence two. Sentence three."
    chunks = ArticleEmbedder().chunk_text(text_with_periods, chunk_size=25)
    for chunk in chunks:
        assert chunk.endswith('.')
    print("✅ Sentence boundary test passed")

    print("\n✅ All chunk_text tests passed!")

if __name__ == "__main__":
    # Run the chunking tests
    test_chunk_text()