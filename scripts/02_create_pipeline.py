# ============================================================================
# The Engineer's RAG Accelerator - Course Code
# Copyright (c) 2026 NeoSage. All rights reserved.
#
# This code is provided exclusively for enrolled students of the RAG Accelerator
# course. It may not be shared, redistributed, or used to create derivative works.
# See the Course Access Policy for full terms.
# ============================================================================

"""
Phase 1: Create FastEmbed Indexing Pipeline (Clean & Simple)
============================================================

A simple, clean pipeline using FastEmbed BAAI/bge-large-en-v1.5 for generating
1024-dimensional embeddings without any rate limiting complexity.

Key Features:
- Uses FastEmbed with BAAI/bge-large-en-v1.5 (1024 dimensions)
- Supports .md, .txt, .py, and .pdf files
- Simple document processing pipeline
- No API rate limits - processes as fast as your CPU allows
- Clean chunking with overlap
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Haystack core imports
from haystack import Pipeline
from haystack.components.converters import MarkdownToDocument, TextFileToDocument, PyPDFToDocument
from haystack.components.preprocessors import DocumentCleaner, DocumentSplitter
from haystack.components.routers import FileTypeRouter
from haystack.components.joiners import DocumentJoiner
from haystack.components.writers import DocumentWriter

# FastEmbed import
from haystack_integrations.components.embedders.fastembed import FastembedDocumentEmbedder

# Qdrant import
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore
from haystack.utils import Secret

# Get project root (script -> rag_pipeline -> week1_foundations -> root)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

def load_environment():
    """Load environment variables."""
    load_dotenv(PROJECT_ROOT / ".env")
    
    # Validate required variables
    required_vars = [
        "QDRANT_URL",
        "QDRANT_API_KEY",
        "QDRANT_COLLECTION_PHASE1",
        "FASTEMBED_MODEL", 
        "EMBEDDING_DIMENSION"
    ]
    
    for var in required_vars:
        if not os.getenv(var):
            raise ValueError(f"Missing required environment variable: {var}")
    
    return {
        "qdrant_url": os.getenv("QDRANT_URL"),
        "qdrant_api_key": os.getenv("QDRANT_API_KEY"),
        "collection_name": os.getenv("QDRANT_COLLECTION_PHASE1"),
        "fastembed_model": os.getenv("FASTEMBED_MODEL", "BAAI/bge-large-en-v1.5"),
        "embedding_dimension": int(os.getenv("EMBEDDING_DIMENSION", "1024")),
        "batch_size": int(os.getenv("FASTEMBED_BATCH_SIZE", "32"))
    }

def create_fastembed_indexing_pipeline(collection_name: str = None):
    """
    Create a clean, simple indexing pipeline using FastEmbed.
    
    Args:
        collection_name (str): Custom collection name
        
    Returns:
        Pipeline: Configured indexing pipeline
        dict: Environment configuration
    """
    env_config = load_environment()
    
    # Use custom collection or default from env
    actual_collection_name = collection_name or env_config["collection_name"]
    
    print("🔧 Creating FastEmbed Indexing Pipeline...")
    print(f"🧠 Model: {env_config['fastembed_model']}")
    print(f"🔢 Dimensions: {env_config['embedding_dimension']}")
    print(f"📊 Collection: {actual_collection_name}")
    print(f"⚡ Batch Size: {env_config['batch_size']}")
    
    # Create Qdrant document store inline
    print("🔧 Creating Qdrant document store...")
    document_store = QdrantDocumentStore(
        url=env_config["qdrant_url"],
        index=actual_collection_name,
        api_key=Secret.from_env_var("QDRANT_API_KEY"),
        embedding_dim=env_config["embedding_dimension"],
        recreate_index=False,  # Connect to existing collection
        return_embedding=True,
        wait_result_from_api=True
    )
    print(f"✅ Connected to Qdrant collection: {actual_collection_name}")
    
    # Create the pipeline
    pipeline = Pipeline()
    
    # 1. File Type Router - routes .md, text files (.txt, .py treated as text/plain), and .pdf files
    pipeline.add_component("file_type_router", FileTypeRouter(mime_types=[
        "text/plain", "text/markdown", "application/pdf"
    ]))
    
    # 2. Document Converters
    pipeline.add_component("text_file_converter", TextFileToDocument())
    pipeline.add_component("markdown_converter", MarkdownToDocument())
    pipeline.add_component("pdf_converter", PyPDFToDocument())
    
    # 3. Document Joiner - combines outputs from both converters
    pipeline.add_component("document_joiner", DocumentJoiner())
    
    # 4. Document Cleaner - clean up the text
    pipeline.add_component("document_cleaner", DocumentCleaner(
        remove_empty_lines=True,
        remove_extra_whitespaces=True,
        remove_repeated_substrings=False  # Keep technical content intact
    ))
    
    # 5. Document Splitter - chunk documents
    pipeline.add_component("document_splitter", DocumentSplitter(
        split_by="word",  # Word-based splitting for technical content
        split_length=400,  # ~2000 characters
        split_overlap=50   # ~250 character overlap
    ))
    
    # 6. FastEmbed Document Embedder - the key component!
    pipeline.add_component("fastembed_embedder", FastembedDocumentEmbedder(
        model=env_config["fastembed_model"],
        batch_size=env_config["batch_size"],
        progress_bar=True,  # Show progress
        parallel=None,  # Use all available CPU cores
    ))
    
    # 7. Document Writer - write to Qdrant
    pipeline.add_component("document_writer", DocumentWriter(document_store=document_store))
    
    # Connect the pipeline components
    print("🔗 Connecting pipeline components...")
    
    # Route files by type
    pipeline.connect("file_type_router.text/plain", "text_file_converter.sources")
    pipeline.connect("file_type_router.text/markdown", "markdown_converter.sources")
    pipeline.connect("file_type_router.application/pdf", "pdf_converter.sources")
    
    # Join documents from all converters
    pipeline.connect("text_file_converter.documents", "document_joiner.documents")
    pipeline.connect("markdown_converter.documents", "document_joiner.documents")
    pipeline.connect("pdf_converter.documents", "document_joiner.documents")
    
    # Process documents
    pipeline.connect("document_joiner.documents", "document_cleaner.documents")
    pipeline.connect("document_cleaner.documents", "document_splitter.documents")
    
    # Generate embeddings and write to Qdrant
    pipeline.connect("document_splitter.documents", "fastembed_embedder.documents")
    pipeline.connect("fastembed_embedder.documents", "document_writer.documents")
    
    print("✅ FastEmbed indexing pipeline created successfully!")
    print("🚀 Ready to process MCP documentation without rate limits!")
    
    return pipeline, env_config

def main():
    """Main function to create and display pipeline structure."""
    try:
        pipeline, env_config = create_fastembed_indexing_pipeline()
        
        print("\n" + "="*60)
        print("📋 FASTEMBED INDEXING PIPELINE SUMMARY")
        print("="*60)
        print(f"🧠 Model: {env_config['fastembed_model']}")
        print(f"🔢 Dimensions: {env_config['embedding_dimension']}")
        print(f"⚡ Batch Size: {env_config['batch_size']}")
        print(f"📊 Collection: {env_config['collection_name']}")
        print("\n🔄 Pipeline Flow:")
        print("   1. FileTypeRouter → Route .md, .txt, .py, and .pdf files")
        print("   2. Converters → Convert files to Documents")
        print("   3. DocumentJoiner → Combine all documents")
        print("   4. DocumentCleaner → Clean up text")
        print("   5. DocumentSplitter → Chunk into manageable pieces")
        print("   6. FastEmbedDocumentEmbedder → Generate 1024-dim embeddings")
        print("   7. DocumentWriter → Store in Qdrant")
        
        print("\n✅ Pipeline ready! Use with 03_run_indexing.py")
        
        # Display pipeline graph
        print("\n🎯 Pipeline Graph:")
        graph = pipeline.graph
        print(f"📊 Components: {len(graph.nodes)}")
        print(f"🔗 Connections: {len(graph.edges)}")
        
        # Validate pipeline structure
        expected_components = [
            "file_type_router", "text_file_converter", "markdown_converter", "pdf_converter",
            "document_joiner", "document_cleaner", "document_splitter",
            "fastembed_embedder", "document_writer"
        ]
        
        missing_components = [comp for comp in expected_components if comp not in graph.nodes]
        if missing_components:
            print(f"⚠️  Missing components: {missing_components}")
        else:
            print("✅ All expected components present")
        
    except Exception as e:
        print(f"❌ Failed to create pipeline: {str(e)}")
        raise

if __name__ == "__main__":
    main()