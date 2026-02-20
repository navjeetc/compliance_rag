# ============================================================================
# The Engineer's RAG Accelerator - Course Code
# Copyright (c) 2026 NeoSage. All rights reserved.
#
# This code is provided exclusively for enrolled students of the RAG Accelerator
# course. It may not be shared, redistributed, or used to create derivative works.
# See the Course Access Policy for full terms.
# ============================================================================

"""
Phase 1: Run FastEmbed Indexing (Test with Subset First)
=======================================================

Process MCP documentation using FastEmbed. Starts with a small subset for testing,
then can scale to full dataset.

Strategy:
1. Test with first 5 markdown files + 1 GitHub digest
2. If successful, process remaining files
3. No rate limiting needed - FastEmbed is local!
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
    Get list of files to process from the three data directories:
    - curated_mcp_knowledge: High-quality curated MCP documentation
    - mcp_docs_crawled: Crawled documentation from official MCP site
    - mcp_python_sdk_filtered: Python SDK examples and source files
    
    Args:
        data_dir (str): Path to data directory
        test_mode (bool): If True, return small subset for testing
        single_dir (str): If specified, only process files from this single subdirectory
        
    Returns:
        List[str]: List of file paths to process
    """
    data_path = Path(data_dir)
    
    if single_dir:
        # Process only files from the specified single directory
        target_path = data_path / single_dir
        if not target_path.exists():
            print(f"❌ Directory {target_path} does not exist!")
            return []
        
        # Get all files from the single directory
        md_files = list(target_path.glob("*.md")) if target_path.exists() else []
        txt_files = list(target_path.glob("*.txt")) if target_path.exists() else []
        pdf_files = list(target_path.glob("*.pdf")) if target_path.exists() else []
        all_files = md_files + txt_files + pdf_files
        
        print(f"📁 Processing single directory: {single_dir}")
        print(f"   - Total files found: {len(all_files)}")
        print(f"   - Markdown files: {len(md_files)}")
        print(f"   - Text files: {len(txt_files)}")
        print(f"   - PDF files: {len(pdf_files)}")
        
        if test_mode and len(all_files) > 10:
            print(f"🧪 TEST MODE: Using first 10 files from {single_dir}")
            return [str(f) for f in all_files[:10]]
        else:
            return [str(f) for f in all_files]
    
    # Original multi-directory logic
    # Get files from curated_mcp_knowledge directory
    curated_path = data_path / "curated_mcp_knowledge" 
    curated_files = list(curated_path.glob("*.md")) if curated_path.exists() else []
    
    # Get files from mcp_docs_crawled directory
    crawled_path = data_path / "mcp_docs_crawled"
    crawled_files = list(crawled_path.glob("*.md")) if crawled_path.exists() else []
    
    # Get files from mcp_python_sdk_filtered directory (both .md and .py files)
    sdk_path = data_path / "mcp_python_sdk_filtered"
    sdk_md_files = list(sdk_path.glob("*.md")) if sdk_path.exists() else []
    sdk_py_files = list(sdk_path.glob("*.py")) if sdk_path.exists() else []
    sdk_txt_files = list(sdk_path.glob("*.txt")) if sdk_path.exists() else []  # Add .txt support
    
    # Get files from raw directory (mainly PDFs for compliance documents)
    raw_path = data_path / "raw"
    raw_pdf_files = list(raw_path.glob("*.pdf")) if raw_path.exists() else []
    
    if test_mode:
        print("🧪 TEST MODE: Processing subset of files")
        # For compliance RAG, prioritize PDF files in test mode
        if raw_pdf_files:
            # Test with 2 PDF files if available
            subset_files = raw_pdf_files[:2]
            print(f"📁 Selected {len(subset_files)} files for testing (PDF focus):")
            print(f"   - Raw PDFs: {len([f for f in subset_files if 'raw' in str(f)])}")
        else:
            # Fallback to original logic if no PDFs
            subset_files = (
                curated_files[:3] +      # 3 curated files
                crawled_files[:5] +      # 5 crawled files  
                sdk_md_files[:2] +       # 2 SDK markdown files
                (sdk_py_files + sdk_txt_files)[:3]  # 3 SDK Python/txt files
            )
            print(f"📁 Selected {len(subset_files)} files for testing:")
            print(f"   - Curated: {len([f for f in subset_files if 'curated_mcp_knowledge' in str(f)])}")
            print(f"   - Crawled: {len([f for f in subset_files if 'mcp_docs_crawled' in str(f)])}")
            print(f"   - SDK MD: {len([f for f in subset_files if 'mcp_python_sdk_filtered' in str(f) and f.suffix == '.md'])}")
            print(f"   - SDK PY/TXT: {len([f for f in subset_files if 'mcp_python_sdk_filtered' in str(f) and f.suffix in ['.py', '.txt']])}")
        return [str(f) for f in subset_files]
    else:
        print("🚀 FULL MODE: Processing all files")
        all_files = curated_files + crawled_files + sdk_md_files + sdk_py_files + sdk_txt_files + raw_pdf_files
        print(f"📁 Total files to process: {len(all_files)}")
        print(f"   - Curated MCP knowledge: {len(curated_files)}")
        print(f"   - Crawled documentation: {len(crawled_files)}")
        print(f"   - SDK markdown files: {len(sdk_md_files)}")
        print(f"   - SDK Python files: {len(sdk_py_files)}")
        print(f"   - SDK Text files: {len(sdk_txt_files)}")
        print(f"   - Raw PDF files: {len(raw_pdf_files)}")
        return [str(f) for f in all_files]

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