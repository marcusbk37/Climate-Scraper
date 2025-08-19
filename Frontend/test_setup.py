#!/usr/bin/env python3
"""
Test script to verify the frontend setup is working correctly.
"""

import sys
import os

# Add the Embedding directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Embedding'))

def test_imports():
    """Test that all required modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        from database import get_db
        print("✅ Database module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import database module: {e}")
        return False
    
    try:
        from embedding import get_embedder
        print("✅ Embedding module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import embedding module: {e}")
        return False
    
    return True

def test_database_connection():
    """Test database connection."""
    print("\n🔍 Testing database connection...")
    
    try:
        from database import get_db
        db = get_db()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_embedder_connection():
    """Test Pinecone connection."""
    print("\n🔍 Testing Pinecone connection...")
    
    try:
        from embedding import get_embedder
        embedder = get_embedder()
        print("✅ Pinecone connection successful")
        return True
    except Exception as e:
        print(f"❌ Pinecone connection failed: {e}")
        return False

def test_search_functionality():
    """Test basic search functionality."""
    print("\n🔍 Testing search functionality...")
    
    try:
        from embedding import get_embedder
        from database import get_db
        
        embedder = get_embedder()
        db = get_db()
        
        # Try a simple search
        results = embedder.search_chunks("test", top_k=1)
        
        if results and results.get('result', {}).get('hits'):
            print(f"✅ Search successful - found {len(results['result']['hits'])} results")
            return True
        else:
            print("⚠️  Search returned no results (this might be normal if no articles exist)")
            return True
            
    except Exception as e:
        print(f"❌ Search functionality failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Frontend Setup Test")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_database_connection,
        test_embedder_connection,
        test_search_functionality
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your frontend is ready to use.")
        print("\nTo start the frontend:")
        print("1. cd Frontend")
        print("2. python app.py")
        print("3. Open http://localhost:5000 in your browser")
    else:
        print("❌ Some tests failed. Please check your setup.")
        print("\nCommon issues:")
        print("- Make sure your .env file is in the Embedding directory")
        print("- Verify your Pinecone and Supabase credentials")
        print("- Ensure all dependencies are installed")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
