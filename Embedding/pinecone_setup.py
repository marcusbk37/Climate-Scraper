# Pinecone setup script
# Add your Pinecone initialization commands here 

import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

# Load environment variables
load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = os.getenv("PINECONE_INDEX_NAME")

if not pc.has_index(index_name):
    pc.create_index_for_model(
        name=index_name,
        cloud="aws",
        region=os.getenv("PINECONE_ENVIRONMENT"),
        embed={
            "model":"llama-text-embed-v2",
            "field_map":{"text": "text"}
        }
    )
    print(f"✅ Created index: {index_name}")
else:
    print(f"✅ Index already exists: {index_name}")

index = pc.Index(index_name)

records = [
    { 
        "_id": "rec1", 
        "text": "The Eiffel Tower was completed in 1889 and stands in Paris, France.", 
        "article_id": "test-article-1",
        "chunk_index": 0,
        "title": "Famous Landmarks",
        "chunk_size": 75,
        "total_chunks": 10,
        "category": "history" 
    },
    { 
        "_id": "rec2", 
        "text": "Photosynthesis allows plants to convert sunlight into energy.", 
        "article_id": "test-article-2",
        "chunk_index": 0,
        "title": "Plant Biology",
        "chunk_size": 67,
        "total_chunks": 10,
        "category": "science" 
    },
    { 
        "_id": "rec3", 
        "text": "Albert Einstein developed the theory of relativity.", 
        "article_id": "test-article-3",
        "chunk_index": 0,
        "title": "Physics History",
        "chunk_size": 58,
        "total_chunks": 10,
        "category": "science" 
    },
    { 
        "_id": "rec4", 
        "text": "The mitochondrion is often called the powerhouse of the cell.", 
        "article_id": "test-article-4",
        "chunk_index": 0,
        "title": "Cell Biology",
        "chunk_size": 71,
        "total_chunks": 10,
        "category": "biology" 
    },
    { 
        "_id": "rec5", 
        "text": "Shakespeare wrote many famous plays, including Hamlet and Macbeth.", 
        "article_id": "test-article-5",
        "chunk_index": 0,
        "title": "Literary Classics",
        "chunk_size": 82,
        "total_chunks": 10,
        "category": "literature" 
    },
    { 
        "_id": "rec6", 
        "text": "Water boils at 100°C under standard atmospheric pressure.", 
        "article_id": "test-article-6",
        "chunk_index": 0,
        "title": "Physics Basics",
        "chunk_size": 69,
        "total_chunks": 10,
        "category": "physics" 
    },
    { 
        "_id": "rec7", 
        "text": "The Great Wall of China was built to protect against invasions.", 
        "article_id": "test-article-7",
        "chunk_index": 0,
        "title": "Ancient History",
        "chunk_size": 73,
        "total_chunks": 10,
        "category": "history" 
    },
    { 
        "_id": "rec8", 
        "text": "Honey never spoils due to its low moisture content and acidity.", 
        "article_id": "test-article-8",
        "chunk_index": 0,
        "title": "Food Science",
        "chunk_size": 76,
        "total_chunks": 10,
        "category": "food science" 
    },
    { 
        "_id": "rec9", 
        "text": "The speed of light in a vacuum is approximately 299,792 km/s.", 
        "article_id": "test-article-9",
        "chunk_index": 0,
        "title": "Physics Constants",
        "chunk_size": 78,
        "total_chunks": 10,
        "category": "physics" 
    },
    { 
        "_id": "rec10", 
        "text": "Newton's laws describe the motion of objects.", 
        "article_id": "test-article-10",
        "chunk_index": 0,
        "title": "Classical Mechanics",
        "chunk_size": 54,
        "total_chunks": 10,
        "category": "physics" 
    }
]

index.upsert_records("ns1", records)

# Print statistics about the index, including:
# - Total number of vectors stored
# - Number of vectors per namespace
# - Index dimensions and settings
print(index.describe_index_stats())

query = "Famous historical structures and monuments"

results = index.search(
    namespace="ns1",
    query={
        "top_k": 5,
        "inputs": {
            'text': query
        }
    }
)

print(results)

reranked_results = index.search(
    namespace="ns1",
    query={
        "top_k": 5,
        "inputs": {
            'text': query
        }
    },
    rerank={
        "model": "bge-reranker-v2-m3",
        "top_n": 5,
        "rank_fields": ["text"]
    },
    fields=["category", "text"]
)

print(reranked_results)