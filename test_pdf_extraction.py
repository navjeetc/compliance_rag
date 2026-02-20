#!/usr/bin/env python3
"""
Test PDF Text Extraction
========================

Simple test to verify we can extract text from our compliance PDFs.
"""

import sys
from pathlib import Path

# Add scripts directory to path
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.append(str(SCRIPT_DIR))

try:
    from haystack.components.converters import PyPDFToDocument
    
    print("🧪 Testing PDF Text Extraction...")
    
    # Get PDF files
    raw_dir = SCRIPT_DIR / "data" / "raw"
    pdf_files = list(raw_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ No PDF files found")
        sys.exit(1)
    
    # Test with first PDF
    test_pdf = pdf_files[0]
    print(f"\n📄 Testing with: {test_pdf.name}")
    
    # Create converter
    converter = PyPDFToDocument()
    
    # Convert PDF to document
    print("🔄 Converting PDF to document...")
    documents = converter.run(sources=[str(test_pdf)])
    
    if documents and documents.get("documents"):
        doc = documents["documents"][0]
        content = doc.content
        
        print(f"✅ Successfully extracted text from {test_pdf.name}")
        print(f"   Document length: {len(content)} characters")
        print(f"   Content preview (first 200 chars):")
        print(f"   {content[:200]}...")
        
        # Test all PDFs
        print(f"\n📊 Testing all {len(pdf_files)} PDFs:")
        for pdf_file in pdf_files:
            try:
                docs = converter.run(sources=[str(pdf_file)])
                if docs and docs.get("documents"):
                    doc = docs["documents"][0]
                    print(f"   ✅ {pdf_file.name}: {len(doc.content)} chars")
                else:
                    print(f"   ❌ {pdf_file.name}: No content extracted")
            except Exception as e:
                print(f"   ❌ {pdf_file.name}: Error - {e}")
    else:
        print(f"❌ Failed to extract text from {test_pdf.name}")
    
    print("\n🎯 PDF extraction test completed!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("   Make sure requirements are installed: pip install -r requirements.txt")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
