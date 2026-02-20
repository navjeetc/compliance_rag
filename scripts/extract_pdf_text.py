#!/usr/bin/env python3
"""
PDF Text Extraction Script
===========================

Extracts raw text from compliance PDFs and saves them as text files.
This is the first step in the Extract → Preprocess → Store pipeline.

Usage:
    python scripts/extract_pdf_text.py
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from haystack.components.converters import PyPDFToDocument


# Project paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
EXTRACTED_DIR = PROJECT_ROOT / "data" / "extracted"

# PDF metadata
PDF_METADATA = {
    "cjis.pdf": {
        "title": "CJIS Security Policy v6.0",
        "type": "compliance_standard",
        "source": "Criminal Justice Information Services",
        "url": "https://drive.google.com/drive/folders/1GQM54O5lpZLKA6zmkiUotpd0HESRQ6_U"
    },
    "SOC2.pdf": {
        "title": "SOC 2 Compliance",
        "type": "compliance_standard",
        "source": "Service Organization Control 2",
        "url": "https://drive.google.com/drive/folders/1GQM54O5lpZLKA6zmkiUotpd0HESRQ6_U"
    },
    "nist.pdf": {
        "title": "NIST SP 800-53 Rev 5.1",
        "type": "compliance_standard",
        "source": "National Institute of Standards and Technology",
        "url": "https://drive.google.com/drive/folders/1GQM54O5lpZLKA6zmkiUotpd0HESRQ6_U"
    },
    "hipaa.pdf": {
        "title": "HIPAA Simplification",
        "type": "compliance_standard",
        "source": "Health Insurance Portability and Accountability Act",
        "url": "https://drive.google.com/drive/folders/1GQM54O5lpZLKA6zmkiUotpd0HESRQ6_U"
    }
}


def ensure_directories():
    """Create necessary directories if they don't exist."""
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 Ensured directory exists: {EXTRACTED_DIR}")


def extract_pdf_text(pdf_path: Path) -> str:
    """
    Extract text from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text content
    """
    print(f"📄 Extracting text from: {pdf_path.name}")
    
    converter = PyPDFToDocument()
    result = converter.run(sources=[str(pdf_path)])
    
    if result and result.get("documents"):
        doc = result["documents"][0]
        text_content = doc.content
        print(f"   ✅ Extracted {len(text_content):,} characters")
        return text_content
    else:
        raise ValueError(f"Failed to extract text from {pdf_path.name}")


def save_extracted_text(filename: str, text: str, metadata: Dict):
    """
    Save extracted text and metadata to files.
    
    Args:
        filename: Original PDF filename
        text: Extracted text content
        metadata: Document metadata
    """
    base_name = filename.replace('.pdf', '')
    
    # Save text file
    text_file = EXTRACTED_DIR / f"{base_name}.txt"
    text_file.write_text(text, encoding='utf-8')
    print(f"   💾 Saved text to: {text_file.name}")
    
    # Save metadata
    metadata_with_extraction = {
        **metadata,
        "extraction_date": datetime.now().isoformat(),
        "original_filename": filename,
        "text_length": len(text),
        "output_file": f"{base_name}.txt"
    }
    
    metadata_file = EXTRACTED_DIR / f"{base_name}_metadata.json"
    metadata_file.write_text(json.dumps(metadata_with_extraction, indent=2), encoding='utf-8')
    print(f"   💾 Saved metadata to: {metadata_file.name}")


def extract_all_pdfs():
    """Extract text from all PDFs in the raw data directory."""
    print("🚀 Starting PDF Text Extraction")
    print("=" * 60)
    
    ensure_directories()
    
    # Get all PDF files
    pdf_files = sorted(RAW_DATA_DIR.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ No PDF files found in data/raw/")
        return
    
    print(f"\n📊 Found {len(pdf_files)} PDF files to process\n")
    
    results = []
    
    for pdf_file in pdf_files:
        try:
            # Extract text
            text = extract_pdf_text(pdf_file)
            
            # Get metadata
            metadata = PDF_METADATA.get(pdf_file.name, {
                "title": pdf_file.stem,
                "type": "unknown",
                "source": "unknown",
                "url": ""
            })
            
            # Save extracted text and metadata
            save_extracted_text(pdf_file.name, text, metadata)
            
            results.append({
                "filename": pdf_file.name,
                "status": "success",
                "text_length": len(text)
            })
            
            print()
            
        except Exception as e:
            print(f"   ❌ Error: {e}\n")
            results.append({
                "filename": pdf_file.name,
                "status": "failed",
                "error": str(e)
            })
    
    # Print summary
    print("=" * 60)
    print("📋 Extraction Summary")
    print("=" * 60)
    
    successful = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] == "failed"]
    
    print(f"✅ Successful: {len(successful)}/{len(results)}")
    print(f"❌ Failed: {len(failed)}/{len(results)}")
    
    if successful:
        print("\n📊 Extracted Documents:")
        total_chars = 0
        for result in successful:
            chars = result["text_length"]
            total_chars += chars
            print(f"   - {result['filename']}: {chars:,} characters")
        print(f"\n   Total: {total_chars:,} characters")
    
    if failed:
        print("\n❌ Failed Documents:")
        for result in failed:
            print(f"   - {result['filename']}: {result['error']}")
    
    print(f"\n💾 Extracted files saved to: {EXTRACTED_DIR}")
    print("\n🎯 Next steps:")
    print("   1. Review extracted text in data/extracted/")
    print("   2. Run preprocessing to clean and normalize the text")
    print("   3. Add metadata enrichment")


if __name__ == "__main__":
    extract_all_pdfs()
