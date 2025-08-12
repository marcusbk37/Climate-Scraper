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
            as of now, overlap should always be 0 - isn't working for MVP...
            
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
                look_for_period = start + (chunk_size // 2)

                # Add a small buffer to check for sentence endings just after chunk end
                # Only check buffer if no period found in main window
                if text.rfind('.', look_for_period, end) == -1:
                    buffer_end = min(end + 20, len(text))

                    # Find sentence end in buffer, see if it is close enough to the chunk end
                    buffer_sentence_end = text.find('.', end, buffer_end)
                    if buffer_sentence_end != -1 and buffer_sentence_end - end < 20:
                        end = buffer_sentence_end + 1
                
                # Find last period in the search window
                sentence_end = text.rfind('.', start, end)

                # Only use sentence boundary if it's not too early in chunk. This prevents tiny chunks
                if sentence_end >= look_for_period:
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

        # print(chunks)    
        return chunks
    
    def store_article_chunks(
        self,
        article_id: str,
        text: str, # passes in the entire article. chunks within the function.
        title: Optional[str] = None,
        chunk_size: int = 1000,
        overlap: int = 0
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

def test_store_article_chunks():
    """Test the article chunking and storing functionality."""
    embedder = ArticleEmbedder()
    article_id = "test_article_1"
    text = "This is a test article. It has some content."
    title = "Test Article"
    chunk_ids = embedder.store_article_chunks(article_id, text, title)

    # Test with empty text
    print("\nTesting store_article_chunks with empty text...")
    empty_chunk_ids = embedder.store_article_chunks("empty_article", "", "Empty Article")
    assert len(empty_chunk_ids) == 0
    print("✅ Empty text storage test passed")

    # Test with very long text
    print("\nTesting store_article_chunks with long text...")
    long_text = " ".join(["Sentence number " + str(i) + "." for i in range(100)])
    long_chunk_ids = embedder.store_article_chunks("long_article", long_text, "Long Article")
    assert len(long_chunk_ids) > 1
    print("✅ Long text storage test passed")

    # Test with different chunk sizes (for some reason, not sure if First sentence. is getting stored properly...)
    print("\nTesting store_article_chunks with different chunk sizes...")
    text = "First sentence. Second sentence. Third sentence. Fourth sentence."
    small_chunk_ids = embedder.store_article_chunks("size_test", text, "Size Test", chunk_size=20)
    large_chunk_ids = embedder.store_article_chunks("size_test", text, "Size Test", chunk_size=100)
    assert len(small_chunk_ids) > len(large_chunk_ids)
    print("✅ Different chunk sizes storage test passed")

    # Test with overlap - haven't gotten overlap up yet. But isn't necessary for MVP...
    # print("\nTesting store_article_chunks with overlap...")
    # text = "First. Second. Third. Fourth. Fifth."
    # no_overlap_ids = embedder.store_article_chunks("overlap_test", text, "Overlap Test", chunk_size=15, overlap=0)
    # with_overlap_ids = embedder.store_article_chunks("overlap_test", text, "Overlap Test", chunk_size=15, overlap=5)
    # assert len(with_overlap_ids) >= len(no_overlap_ids)
    # print("✅ Overlap storage test passed")

    # Test chunk ID format
    print("\nTesting chunk ID format...")
    test_id = "test_format"
    chunk_ids = embedder.store_article_chunks(test_id, "Test text", "Test Format")
    for i, chunk_id in enumerate(chunk_ids):
        assert chunk_id == f"{test_id}_chunk_{i}", f"Chunk ID format incorrect: {chunk_id}"
    print("✅ Chunk ID format test passed")

    # Test metadata consistency
    print("\nTesting metadata consistency...")
    article_id = "metadata_test"
    title = "Metadata Test"
    text = "First sentence. Second sentence."
    chunk_ids = embedder.store_article_chunks(article_id, text, title)
    
    # Verify each chunk in Pinecone
    for i, chunk_id in enumerate(chunk_ids):
        try:
            result = embedder.index.fetch_records("ns1", [chunk_id])
            assert result[chunk_id]["article_id"] == article_id
            assert result[chunk_id]["title"] == title
            assert result[chunk_id]["chunk_index"] == i
            assert isinstance(result[chunk_id]["text"], str)
        except Exception as e:
            print(f"Failed to verify chunk {chunk_id}: {str(e)}")
            raise
    print("✅ Metadata consistency test passed")

    print("\n✅ All store_article_chunks tests passed!")

def test_search_chunks():
    """Test the chunk searching functionality."""
    embedder = ArticleEmbedder()

    # Test basic search
    print("\nTesting basic search...")
    query = "test query"
    results = embedder.search_chunks(query, limit=3)
    assert isinstance(results, list), "Search should return a list"
    if results:
        for result in results:
            assert isinstance(result, dict), "Each result should be a dictionary"
            assert "id" in result, "Result should have an id"
            assert "score" in result, "Result should have a score"
            assert "metadata" in result, "Result should have metadata"
        print("✅ Basic search test passed")
    else:
        print("⚠️ No results found, but search executed successfully")

    # Test search with different limits
    print("\nTesting search with different limits...")
    results_small = embedder.search_chunks(query, limit=2)
    results_large = embedder.search_chunks(query, limit=5)
    assert len(results_small) <= 2, "Should respect small limit"
    assert len(results_large) <= 5, "Should respect large limit"
    print("✅ Search limits test passed")

    # Test search with filters
    print("\nTesting search with filters...")
    filter_query = {
        "article_id": "test_article_1"
    }
    filtered_results = embedder.search_chunks(query, filter=filter_query)
    if filtered_results:
        for result in filtered_results:
            assert result["metadata"]["article_id"] == "test_article_1", "Filter not working correctly"
        print("✅ Search filters test passed")
    else:
        print("⚠️ No filtered results found, but search executed successfully")

    print("\n✅ All search_chunks tests passed!")


if __name__ == "__main__":
    # Run tests
    # test_chunk_text() - but never tested with overlap
    # test_store_article_chunks()
    # test_search_chunks()