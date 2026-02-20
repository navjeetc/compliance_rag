#!/usr/bin/env python3
"""
Test Retrieval from Qdrant
===========================

Quick test to verify document retrieval from Qdrant collection.
Tests semantic search and citation retrieval.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore
from haystack_integrations.components.retrievers.qdrant import QdrantEmbeddingRetriever
from haystack_integrations.components.embedders.fastembed import FastembedTextEmbedder
from haystack import Pipeline
from haystack.utils import Secret

# Project paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR

# Load environment
load_dotenv(PROJECT_ROOT / ".env")

def test_retrieval():
    """Test document retrieval from Qdrant."""
    print("🧪 Testing Document Retrieval from Qdrant")
    print("=" * 60)
    
    # Configuration
    collection_name = os.getenv("QDRANT_COLLECTION_PHASE1")
    qdrant_url = os.getenv("QDRANT_URL")
    
    print(f"\n📊 Configuration:")
    print(f"   Collection: {collection_name}")
    print(f"   URL: {qdrant_url}")
    
    # Initialize document store
    print(f"\n🔗 Connecting to Qdrant...")
    embedding_dim = int(os.getenv("EMBEDDING_DIMENSION", "1024"))
    document_store = QdrantDocumentStore(
        url=qdrant_url,
        api_key=Secret.from_env_var("QDRANT_API_KEY"),
        index=collection_name,
        embedding_dim=embedding_dim,
        return_embedding=False,
        wait_result_from_api=True,
    )
    
    # Check document count
    doc_count = document_store.count_documents()
    print(f"   ✅ Connected! Documents in collection: {doc_count}")
    
    if doc_count == 0:
        print(f"\n❌ No documents found in collection!")
        print(f"   Run indexing first: python scripts/03_run_indexing.py --test")
        return
    
    # Create retrieval pipeline
    print(f"\n🔧 Creating retrieval pipeline...")
    
    text_embedder = FastembedTextEmbedder(
        model="BAAI/bge-large-en-v1.5",
        progress_bar=False
    )
    
    retriever = QdrantEmbeddingRetriever(
        document_store=document_store,
        top_k=5
    )
    
    pipeline = Pipeline()
    pipeline.add_component("text_embedder", text_embedder)
    pipeline.add_component("retriever", retriever)
    pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
    
    print(f"   ✅ Pipeline created")
    
    # Test queries
    test_queries = [
        "What are the access control requirements?",
        "What are the authentication requirements for CJIS?",
        "What are the audit logging requirements?",
    ]
    
    print(f"\n🔍 Testing Retrieval with Sample Queries")
    print("=" * 60)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Query {i}: {query}")
        print("-" * 60)
        
        # Run query
        result = pipeline.run({
            "text_embedder": {"text": query}
        })
        
        documents = result["retriever"]["documents"]
        
        if not documents:
            print("   ❌ No documents retrieved")
            continue
        
        print(f"   ✅ Retrieved {len(documents)} documents")
        
        # Show top 3 results
        for j, doc in enumerate(documents[:3], 1):
            content_preview = doc.content[:150].replace('\n', ' ')
            score = doc.score if hasattr(doc, 'score') else 'N/A'
            source = doc.meta.get('file_path', 'Unknown') if doc.meta else 'Unknown'
            
            print(f"\n   Result {j}:")
            print(f"   Score: {score}")
            print(f"   Source: {Path(source).name if source != 'Unknown' else 'Unknown'}")
            print(f"   Preview: {content_preview}...")
    
    print("\n" + "=" * 60)
    print("🎉 Retrieval test completed!")
    print("=" * 60)
    
    print(f"\n📊 Summary:")
    print(f"   - Total documents in collection: {doc_count}")
    print(f"   - Test queries executed: {len(test_queries)}")
    print(f"   - Retrieval pipeline: Working ✅")
    
    print(f"\n🎯 Next Steps:")
    print(f"   1. Run full indexing: python scripts/03_run_indexing.py")
    print(f"   2. Test RAG system: python scripts/04_test_rag_system.py")
    print(f"   3. Try interactive queries: python scripts/05_interactive_rag.py")


if __name__ == "__main__":
    try:
        test_retrieval()
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
