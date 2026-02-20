#!/usr/bin/env python3
"""
Test PDF Processing Pipeline
============================

Test script to verify PDF processing works with our compliance documents.
"""

import sys
from pathlib import Path

# Add scripts directory to path
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.append(str(SCRIPT_DIR))

try:
    # Import from scripts directory
    import importlib.util
    
    # Import create_pipeline
    pipeline_path = SCRIPT_DIR / "scripts" / "02_create_pipeline.py"
    spec = importlib.util.spec_from_file_location("create_pipeline", pipeline_path)
    create_pipeline_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(create_pipeline_module)
    create_fastembed_indexing_pipeline = create_pipeline_module.create_fastembed_indexing_pipeline
    
    # Import run_indexing
    indexing_path = SCRIPT_DIR / "scripts" / "03_run_indexing.py"
    spec = importlib.util.spec_from_file_location("run_indexing", indexing_path)
    indexing_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(indexing_module)
    get_file_subset = indexing_module.get_file_subset
    
    print("🧪 Testing PDF Pipeline Components...")
    
    # Test 1: Create pipeline
    print("\n1. Testing pipeline creation...")
    try:
        pipeline, env_config = create_fastembed_indexing_pipeline("test_collection")
        print("✅ Pipeline created successfully!")
        print(f"   Model: {env_config['fastembed_model']}")
        print(f"   Dimensions: {env_config['embedding_dimension']}")
    except Exception as e:
        print(f"❌ Pipeline creation failed: {e}")
        print("   This is expected if Qdrant credentials are not set up")
    
    # Test 2: File discovery
    print("\n2. Testing PDF file discovery...")
    data_dir = SCRIPT_DIR / "data"
    pdf_files = get_file_subset(str(data_dir), test_mode=True, single_dir="raw")
    
    if pdf_files:
        print(f"✅ Found {len(pdf_files)} PDF files:")
        for i, file in enumerate(pdf_files, 1):
            print(f"   {i}. {Path(file).name}")
    else:
        print("❌ No PDF files found in data/raw/")
    
    print("\n🎯 Test completed!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("   Make sure requirements are installed: pip install -r requirements.txt")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
