# ============================================================================
# The Engineer's RAG Accelerator - Course Code
# Copyright (c) 2026 NeoSage. All rights reserved.
#
# This code is provided exclusively for enrolled students of the RAG Accelerator
# course. It may not be shared, redistributed, or used to create derivative works.
# See the Course Access Policy for full terms.
# ============================================================================

"""
Compliance RAG: Run FastEmbed Indexing
======================================

Process compliance documents using FastEmbed. Starts with a small subset for testing,
then can scale to full dataset.

Strategy:
1. Test with first 2 processed compliance documents
2. If successful, process all 4 documents
3. No rate limiting needed - FastEmbed is local!

Documents:
- CJIS Security Policy
- SOC 2 Compliance
- NIST SP 800-53
- HIPAA Simplification
"""

import os
import time
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from tqdm import tqdm

# Get project root (script -> scripts -> root)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

# Import from renamed module in current directory
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import from renamed module (need to import dynamically)
import importlib.util
module_path = os.path.join(os.path.dirname(__file__), "02_create_pipeline.py")
spec = importlib.util.spec_from_file_location("create_pipeline", module_path)
create_pipeline_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(create_pipeline_module)
create_fastembed_indexing_pipeline = create_pipeline_module.create_fastembed_indexing_pipeline

def get_file_subset(data_dir: str, test_mode: bool = True, single_dir: str = None) -> List[str]:
    """
    Get list of processed compliance documents to index.
    Uses preprocessed text files from data/processed/ directory.
    
    Args:
        data_dir (str): Path to data directory
        test_mode (bool): If True, return small subset for testing
        single_dir (str): If specified, only process files from this single subdirectory
        
    Returns:
        List[str]: List of file paths to process
    """
    data_path = Path(data_dir)
    
    # Use processed directory for compliance documents
    processed_path = data_path / "processed"
    
    if not processed_path.exists():
        print(f"❌ Processed directory not found: {processed_path}")
        print(f"   Run preprocessing first: python scripts/preprocess_text.py")
        return []
    
    # Get all processed text files (exclude metadata JSON files)
    txt_files = sorted([f for f in processed_path.glob("*.txt")])
    
    if not txt_files:
        print(f"❌ No processed text files found in {processed_path}")
        return []
    
    print(f"📁 Found {len(txt_files)} processed compliance documents:")
    for f in txt_files:
        print(f"   - {f.name}")
    
    if test_mode:
        # In test mode, use first 2 documents
        subset_files = txt_files[:2]
        print(f"\n🧪 TEST MODE: Using {len(subset_files)} documents for testing")
        for f in subset_files:
            print(f"   ✓ {f.name}")
        return [str(f) for f in subset_files]
    else:
        print(f"\n🚀 FULL MODE: Processing all {len(txt_files)} documents")
        return [str(f) for f in txt_files]

def run_fastembed_indexing(collection_name: str = None, test_mode: bool = True, single_dir: str = None):
    """
    Run the FastEmbed indexing pipeline.
    
    Args:
        collection_name (str): Custom collection name
        test_mode (bool): If True, process only subset of files
        single_dir (str): If specified, process only files from this directory (e.g., 'mcp_python_sdk_filtered')
    """
    load_dotenv(PROJECT_ROOT / ".env")

    # Get data directory (always relative to project root)
    data_dir = str(PROJECT_ROOT / "data")

    print(f"📂 Looking for data in: {data_dir}")
    files_to_process = get_file_subset(data_dir, test_mode, single_dir)
    
    if not files_to_process:
        print("❌ No files found to process!")
        return
    
    print("\n🔧 Creating FastEmbed indexing pipeline...")
    
    try:
        # Create the pipeline
        pipeline, env_config = create_fastembed_indexing_pipeline(collection_name)
        
        print(f"\n🚀 Starting indexing process...")
        print(f"🧠 Model: {env_config['fastembed_model']}")
        print(f"📊 Target Collection: {collection_name or env_config['collection_name']}")
        print(f"📁 Files to process: {len(files_to_process)}")
        
        start_time = time.time()
        
        # Run the pipeline
        print("\n⚡ Processing files (no rate limits with FastEmbed!)...")
        
        result = pipeline.run(
            data={
                "file_type_router": {"sources": files_to_process}
            }
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Display results
        print(f"\n✅ FastEmbed indexing completed!")
        print(f"⏱️  Total processing time: {processing_time:.2f} seconds")
        print(f"📊 Average time per file: {processing_time/len(files_to_process):.2f} seconds")
        
        # Check if documents were written
        documents_written = result.get("document_writer", {}).get("documents_written", 0)
        if documents_written:
            print(f"📝 Documents written to Qdrant: {documents_written}")
        
        print("\n🎯 Next steps:")
        if test_mode:
            print("1. Verify documents in Qdrant")
            print("2. Test RAG queries")
            print("3. If successful, run with test_mode=False for full dataset")
        else:
            print("1. All documents indexed successfully!")
            print("2. Ready for RAG queries")
            print("3. Test with test_fastembed_rag.py")
            
        return result
        
    except Exception as e:
        print(f"❌ FastEmbed indexing failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

def main():
    """Main function with command line options."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run FastEmbed indexing for MCP RAG")
    parser.add_argument("--collection", help="Custom collection name")
    parser.add_argument("--full", action="store_true", help="Process all files (~250 files, 5-10 minutes)")
    parser.add_argument("--test", action="store_true", help="Process test subset only (~13 files, 30-60 seconds) [DEFAULT]")
    parser.add_argument("--single-dir", help="Process only files from single directory (e.g., 'mcp_python_sdk_filtered')")
    
    args = parser.parse_args()
    
    # Determine test mode
    if args.full:
        test_mode = False
    else:
        test_mode = True  # Default to test mode
    
    print("🚀 FastEmbed Indexing for MCP RAG")
    print("=" * 50)
    
    mode_str = "TEST (subset)" if test_mode else "FULL (all files)"
    if args.single_dir:
        mode_str = f"SINGLE DIR: {args.single_dir}"
    print(f"🎯 Mode: {mode_str}")
    
    if args.collection:
        print(f"📊 Collection: {args.collection}")
    
    try:
        result = run_fastembed_indexing(
            collection_name=args.collection,
            test_mode=test_mode,
            single_dir=args.single_dir
        )
        
        print("\n🎉 Indexing completed successfully!")
        
    except Exception as e:
        print(f"\n💥 Indexing failed: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()