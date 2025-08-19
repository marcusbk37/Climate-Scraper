#!/usr/bin/env python3

import pinecone
print(f"Pinecone version: {pinecone.__version__}")

# Also check what methods are available
pc = pinecone.Pinecone(api_key="test")
print(f"Pinecone client type: {type(pc)}")

# Try to create an index object to see what methods it has
try:
    index = pc.Index("test")
    print(f"Index type: {type(index)}")
    print(f"Index methods: {[method for method in dir(index) if not method.startswith('_')]}")
except Exception as e:
    print(f"Error creating index: {e}")
