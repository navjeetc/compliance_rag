#!/usr/bin/env python3
"""
Text Preprocessing Script
==========================

Cleans and normalizes extracted text from compliance PDFs.
This is the second step in the Extract → Preprocess → Store pipeline.

Preprocessing steps:
1. Remove excessive whitespace and empty lines
2. Normalize line breaks and formatting
3. Remove page numbers and headers/footers
4. Clean up table of contents artifacts
5. Preserve document structure and important formatting

Usage:
    python scripts/preprocess_text.py
"""

import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple


# Project paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
EXTRACTED_DIR = PROJECT_ROOT / "data" / "extracted"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def ensure_directories():
    """Create necessary directories if they don't exist."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 Ensured directory exists: {PROCESSED_DIR}")


def remove_excessive_whitespace(text: str) -> str:
    """Remove excessive whitespace while preserving paragraph structure."""
    # Replace multiple spaces with single space
    text = re.sub(r' {2,}', ' ', text)
    
    # Replace multiple newlines with max 2 newlines (preserve paragraph breaks)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove trailing whitespace from each line
    lines = [line.rstrip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    return text


def remove_page_artifacts(text: str) -> str:
    """Remove common page artifacts like page numbers, headers, footers."""
    lines = text.split('\n')
    cleaned_lines = []
    
    for i, line in enumerate(lines):
        # Skip lines that are just page numbers (e.g., "1", "Page 1", "- 1 -")
        if re.match(r'^\s*[-–—]?\s*\d+\s*[-–—]?\s*$', line):
            continue
        
        # Skip lines that look like "Page X of Y"
        if re.match(r'^\s*Page\s+\d+\s*(of\s+\d+)?\s*$', line, re.IGNORECASE):
            continue
        
        # Skip very short lines at the beginning or end that might be headers/footers
        if len(line.strip()) < 3 and (i < 5 or i > len(lines) - 5):
            continue
        
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


def normalize_section_headers(text: str) -> str:
    """Normalize section headers and numbering."""
    lines = text.split('\n')
    normalized_lines = []
    
    for line in lines:
        # Normalize section numbers (e.g., "1.1.1" followed by text)
        # Add consistent spacing after section numbers
        line = re.sub(r'^(\d+(?:\.\d+)*)\s*([A-Z])', r'\1 \2', line)
        
        normalized_lines.append(line)
    
    return '\n'.join(normalized_lines)


def remove_table_of_contents_artifacts(text: str) -> str:
    """Remove table of contents page number references and dot leaders."""
    # Remove dot leaders (e.g., "Introduction ........ 5")
    text = re.sub(r'\.{3,}\s*\d+', '', text)
    
    # Remove standalone page numbers at end of lines in TOC
    text = re.sub(r'\s+\d+\s*$', '', text, flags=re.MULTILINE)
    
    return text


def clean_special_characters(text: str) -> str:
    """Clean up special characters and encoding issues."""
    # Replace common PDF extraction artifacts
    replacements = {
        '\x00': '',  # Null bytes
        '\ufeff': '',  # BOM
        '\u200b': '',  # Zero-width space
        '\u00a0': ' ',  # Non-breaking space to regular space
        '–': '-',  # En dash to hyphen
        '—': '-',  # Em dash to hyphen
        '"': '"',  # Smart quotes to regular quotes
        '"': '"',
        ''': "'",
        ''': "'",
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text


def preprocess_text(text: str) -> str:
    """
    Apply all preprocessing steps to the text.
    
    Args:
        text: Raw extracted text
        
    Returns:
        Preprocessed and cleaned text
    """
    # Apply preprocessing steps in order
    text = clean_special_characters(text)
    text = remove_page_artifacts(text)
    text = remove_table_of_contents_artifacts(text)
    text = normalize_section_headers(text)
    text = remove_excessive_whitespace(text)
    
    # Final cleanup: strip leading/trailing whitespace
    text = text.strip()
    
    return text


def calculate_stats(original: str, processed: str) -> Dict:
    """Calculate statistics about the preprocessing."""
    return {
        "original_length": len(original),
        "processed_length": len(processed),
        "reduction_chars": len(original) - len(processed),
        "reduction_percent": round((1 - len(processed) / len(original)) * 100, 2) if len(original) > 0 else 0,
        "original_lines": original.count('\n') + 1,
        "processed_lines": processed.count('\n') + 1
    }


def process_document(text_file: Path) -> Tuple[str, Dict]:
    """
    Process a single document.
    
    Args:
        text_file: Path to the extracted text file
        
    Returns:
        Tuple of (processed_text, stats)
    """
    print(f"📄 Processing: {text_file.name}")
    
    # Read original text
    original_text = text_file.read_text(encoding='utf-8')
    
    # Preprocess
    processed_text = preprocess_text(original_text)
    
    # Calculate stats
    stats = calculate_stats(original_text, processed_text)
    
    print(f"   ✅ Reduced by {stats['reduction_chars']:,} chars ({stats['reduction_percent']}%)")
    print(f"   📊 {stats['original_length']:,} → {stats['processed_length']:,} characters")
    
    return processed_text, stats


def save_processed_document(filename: str, text: str, metadata: Dict, stats: Dict):
    """
    Save processed text and updated metadata.
    
    Args:
        filename: Original filename (without .txt extension)
        text: Processed text
        metadata: Original metadata
        stats: Processing statistics
    """
    # Save processed text
    text_file = PROCESSED_DIR / f"{filename}.txt"
    text_file.write_text(text, encoding='utf-8')
    print(f"   💾 Saved to: {text_file.name}")
    
    # Update metadata with preprocessing info
    updated_metadata = {
        **metadata,
        "preprocessing_date": datetime.now().isoformat(),
        "preprocessing_stats": stats,
        "processed_file": f"{filename}.txt"
    }
    
    metadata_file = PROCESSED_DIR / f"{filename}_metadata.json"
    metadata_file.write_text(json.dumps(updated_metadata, indent=2), encoding='utf-8')
    print(f"   💾 Saved metadata to: {metadata_file.name}")


def preprocess_all_documents():
    """Preprocess all extracted documents."""
    print("🚀 Starting Text Preprocessing")
    print("=" * 60)
    
    ensure_directories()
    
    # Get all extracted text files
    text_files = sorted(EXTRACTED_DIR.glob("*.txt"))
    
    if not text_files:
        print("❌ No text files found in data/extracted/")
        return
    
    print(f"\n📊 Found {len(text_files)} text files to process\n")
    
    results = []
    total_original = 0
    total_processed = 0
    
    for text_file in text_files:
        try:
            # Load metadata
            metadata_file = EXTRACTED_DIR / f"{text_file.stem}_metadata.json"
            if metadata_file.exists():
                metadata = json.loads(metadata_file.read_text(encoding='utf-8'))
            else:
                metadata = {"title": text_file.stem}
            
            # Process document
            processed_text, stats = process_document(text_file)
            
            # Save processed document
            save_processed_document(text_file.stem, processed_text, metadata, stats)
            
            results.append({
                "filename": text_file.name,
                "status": "success",
                "stats": stats
            })
            
            total_original += stats["original_length"]
            total_processed += stats["processed_length"]
            
            print()
            
        except Exception as e:
            print(f"   ❌ Error: {e}\n")
            results.append({
                "filename": text_file.name,
                "status": "failed",
                "error": str(e)
            })
    
    # Print summary
    print("=" * 60)
    print("📋 Preprocessing Summary")
    print("=" * 60)
    
    successful = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] == "failed"]
    
    print(f"✅ Successful: {len(successful)}/{len(results)}")
    print(f"❌ Failed: {len(failed)}/{len(results)}")
    
    if successful:
        print("\n📊 Processing Statistics:")
        print(f"   Original total: {total_original:,} characters")
        print(f"   Processed total: {total_processed:,} characters")
        reduction = total_original - total_processed
        reduction_pct = (reduction / total_original * 100) if total_original > 0 else 0
        print(f"   Total reduction: {reduction:,} characters ({reduction_pct:.2f}%)")
        
        print("\n📄 Individual Documents:")
        for result in successful:
            stats = result["stats"]
            print(f"   - {result['filename']}: {stats['reduction_percent']}% reduction")
    
    if failed:
        print("\n❌ Failed Documents:")
        for result in failed:
            print(f"   - {result['filename']}: {result['error']}")
    
    print(f"\n💾 Processed files saved to: {PROCESSED_DIR}")
    print("\n🎯 Next steps:")
    print("   1. Review processed text in data/processed/")
    print("   2. Add metadata enrichment")
    print("   3. Run the indexing pipeline")


if __name__ == "__main__":
    preprocess_all_documents()
