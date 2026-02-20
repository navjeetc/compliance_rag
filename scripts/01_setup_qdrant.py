# ============================================================================
# The Engineer's RAG Accelerator - Course Code
# Copyright (c) 2026 NeoSage. All rights reserved.
#
# This code is provided exclusively for enrolled students of the RAG Accelerator
# course. It may not be shared, redistributed, or used to create derivative works.
# See the Course Access Policy for full terms.
# ============================================================================

"""
Phase 1: Setup Qdrant Document Store (Updated)
==============================================

This module initializes a QdrantDocumentStore connection with support for custom collection names.

Usage:
    # Default collection from .env
    python setup_qdrant_store.py
    
    # Custom collection for testing
    python setup_qdrant_store.py --collection compliance_rag_test
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Import the correct packages from latest documentation
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore
from haystack.utils import Secret

# Get project root (script -> scripts -> root)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

def load_environment() -> dict:
    """Load environment variables and validate required settings."""
    load_dotenv(PROJECT_ROOT / ".env")
    
    # Required environment variables
    required_vars = [
        "QDRANT_URL",
        "QDRANT_API_KEY", 
        "QDRANT_COLLECTION_PHASE1",
        "EMBEDDING_DIMENSION"
    ]
    
    env_vars = {}
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        env_vars[var] = value
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {missing_vars}")
    
    return env_vars

def create_qdrant_document_store(collection_name: str = None, recreate_index: bool = True) -> QdrantDocumentStore:
    """
    Create and configure QdrantDocumentStore for MCP documentation.
    
    Args:
        collection_name (str): Custom collection name (overrides env var if provided)
        recreate_index (bool): Whether to recreate the index. Set True for fresh start.
                              Set False to connect to existing collection.
    
    Returns:
        QdrantDocumentStore: Configured document store instance
    """
    env_vars = load_environment()
    
    # Use custom collection name or fall back to env default
    actual_collection_name = collection_name or env_vars["QDRANT_COLLECTION_PHASE1"]
    
    print("🔧 Initializing Qdrant Document Store...")
    print(f"📡 Connecting to: {env_vars['QDRANT_URL']}")
    print(f"📊 Collection: {actual_collection_name}")
    print(f"🔢 Embedding Dimensions: {env_vars['EMBEDDING_DIMENSION']}")
    print(f"🔄 Recreate Index: {recreate_index}")
    
    try:
        # Create QdrantDocumentStore using latest documented syntax
        document_store = QdrantDocumentStore(
            url=env_vars["QDRANT_URL"],
            index=actual_collection_name,  # Use actual collection name
            api_key=Secret.from_env_var("QDRANT_API_KEY"),
            embedding_dim=int(env_vars["EMBEDDING_DIMENSION"]),
            recreate_index=recreate_index,
            return_embedding=True,  # Important for retrieval
            wait_result_from_api=True,  # Ensures writes are confirmed
            # Optional: Configure HNSW for performance
            hnsw_config={
                "m": 16,          # Number of connections
                "ef_construct": 200,  # Search width during construction
            }
        )
        
        print("✅ Qdrant Document Store initialized successfully!")
        return document_store
        
    except Exception as e:
        print(f"❌ Failed to initialize Qdrant Document Store: {str(e)}")
        print("🔍 Please check:")
        print("   - Qdrant URL is correct and accessible")
        print("   - API key is valid")
        print("   - Network connectivity to Qdrant Cloud")
        raise

def test_connection(document_store: QdrantDocumentStore) -> bool:
    """
    Test the Qdrant connection by checking basic operations.
    
    Args:
        document_store (QdrantDocumentStore): The document store to test
        
    Returns:
        bool: True if connection works, False otherwise
    """
    try:
        # Test basic connection
        count = document_store.count_documents()
        print(f"🔍 Current documents in collection: {count}")
        
        # Test with a sample document if empty
        if count == 0:
            from haystack.dataclasses import Document
            
            test_doc = Document(
                content="This is a test document for Compliance RAG system.",
                meta={"test": True, "source": "connection_test"}
            )
            
            print("📄 Writing test document...")
            document_store.write_documents([test_doc])
            
            new_count = document_store.count_documents()
            print(f"✅ Test document written. New count: {new_count}")
            
            # Clean up test document
            # Note: In production, you'd filter and delete the test doc
            print("🧹 Test completed (test document will remain for now)")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {str(e)}")
        return False

def main():
    """Main function to setup and test Qdrant Document Store with command line support."""
    parser = argparse.ArgumentParser(description="Setup Qdrant Document Store for Compliance RAG")
    parser.add_argument("--collection", help="Custom collection name (overrides .env setting)")
    parser.add_argument("--no-recreate", action="store_true", help="Don't recreate index (connect to existing)")
    
    args = parser.parse_args()
    
    # Determine collection name
    collection_name = args.collection
    recreate_index = not args.no_recreate
    
    print("🚀 Phase 1: Setting up Qdrant Document Store for Compliance RAG")
    if collection_name:
        print(f"🎯 Using custom collection: {collection_name}")
    else:
        print("🎯 Using default collection from .env")
    print("=" * 60)
    
    try:
        # Create document store
        document_store = create_qdrant_document_store(
            collection_name=collection_name,
            recreate_index=recreate_index
        )
        
        # Test connection
        if test_connection(document_store):
            print("\n✅ Qdrant Document Store setup completed successfully!")
            print("🎯 Ready for Phase 1 indexing pipeline.")
            if collection_name:
                print(f"📊 Collection '{collection_name}' is ready for use.")
        else:
            print("\n❌ Setup completed but connection test failed.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Setup failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()