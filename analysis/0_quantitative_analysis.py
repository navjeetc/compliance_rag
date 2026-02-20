#!/usr/bin/env python3
"""
Quantitative Analysis of Compliance Documents
==============================================

Analyzes the compliance corpus for:
- Document count and total size
- Distribution of document lengths
- File formats present
- Duplicate detection
- Basic statistics

This provides a baseline understanding of the corpus before indexing.
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple
import json
from collections import defaultdict
import hashlib

def get_project_root() -> Path:
    """Get project root directory"""
    return Path(__file__).resolve().parent.parent

def analyze_documents(data_dir: Path) -> Dict:
    """Analyze all documents in the corpus"""
    
    results = {
        "raw_documents": {},
        "extracted_documents": {},
        "processed_documents": {},
        "statistics": {},
        "duplicates": []
    }
    
    # Analyze raw PDFs
    raw_dir = data_dir / "raw"
    if raw_dir.exists():
        pdf_files = list(raw_dir.glob("*.pdf"))
        results["raw_documents"] = {
            "count": len(pdf_files),
            "files": [],
            "total_size_bytes": 0,
            "total_size_mb": 0
        }
        
        for pdf in pdf_files:
            size = pdf.stat().st_size
            results["raw_documents"]["files"].append({
                "name": pdf.name,
                "size_bytes": size,
                "size_mb": round(size / (1024 * 1024), 2)
            })
            results["raw_documents"]["total_size_bytes"] += size
        
        results["raw_documents"]["total_size_mb"] = round(
            results["raw_documents"]["total_size_bytes"] / (1024 * 1024), 2
        )
    
    # Analyze extracted text files
    extracted_dir = data_dir / "extracted"
    if extracted_dir.exists():
        txt_files = list(extracted_dir.glob("*.txt"))
        results["extracted_documents"] = {
            "count": len(txt_files),
            "files": [],
            "total_characters": 0,
            "character_distribution": []
        }
        
        char_counts = []
        for txt_file in txt_files:
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read()
                char_count = len(content)
                char_counts.append(char_count)
                
                results["extracted_documents"]["files"].append({
                    "name": txt_file.name,
                    "characters": char_count,
                    "lines": content.count('\n'),
                    "words": len(content.split())
                })
                results["extracted_documents"]["total_characters"] += char_count
        
        if char_counts:
            results["extracted_documents"]["character_distribution"] = {
                "min": min(char_counts),
                "max": max(char_counts),
                "average": round(sum(char_counts) / len(char_counts), 0)
            }
    
    # Analyze processed text files
    processed_dir = data_dir / "processed"
    if processed_dir.exists():
        txt_files = list(processed_dir.glob("*.txt"))
        results["processed_documents"] = {
            "count": len(txt_files),
            "files": [],
            "total_characters": 0,
            "character_distribution": []
        }
        
        char_counts = []
        for txt_file in txt_files:
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read()
                char_count = len(content)
                char_counts.append(char_count)
                
                results["processed_documents"]["files"].append({
                    "name": txt_file.name,
                    "characters": char_count,
                    "lines": content.count('\n'),
                    "words": len(content.split())
                })
                results["processed_documents"]["total_characters"] += char_count
        
        if char_counts:
            results["processed_documents"]["character_distribution"] = {
                "min": min(char_counts),
                "max": max(char_counts),
                "average": round(sum(char_counts) / len(char_counts), 0)
            }
    
    # Calculate statistics
    if results["extracted_documents"]["total_characters"] > 0 and results["processed_documents"]["total_characters"] > 0:
        reduction = results["extracted_documents"]["total_characters"] - results["processed_documents"]["total_characters"]
        reduction_pct = (reduction / results["extracted_documents"]["total_characters"]) * 100
        
        results["statistics"] = {
            "extraction_to_processing_reduction": {
                "characters_removed": reduction,
                "percentage": round(reduction_pct, 2)
            }
        }
    
    # Check for duplicates (by content hash)
    content_hashes = defaultdict(list)
    
    for txt_file in (processed_dir / "*.txt").parent.glob("*.txt") if processed_dir.exists() else []:
        with open(txt_file, 'r', encoding='utf-8') as f:
            content = f.read()
            content_hash = hashlib.md5(content.encode()).hexdigest()
            content_hashes[content_hash].append(txt_file.name)
    
    duplicates = [files for files in content_hashes.values() if len(files) > 1]
    results["duplicates"] = duplicates if duplicates else []
    
    return results

def print_analysis_report(results: Dict):
    """Print formatted analysis report"""
    
    print("\n" + "="*60)
    print("📊 QUANTITATIVE ANALYSIS OF COMPLIANCE CORPUS")
    print("="*60)
    
    # Raw documents
    if results["raw_documents"]:
        print(f"\n📄 Raw PDF Documents:")
        print(f"   Count: {results['raw_documents']['count']}")
        print(f"   Total Size: {results['raw_documents']['total_size_mb']} MB")
        print(f"\n   Files:")
        for file in results["raw_documents"]["files"]:
            print(f"   - {file['name']}: {file['size_mb']} MB")
    
    # Extracted documents
    if results["extracted_documents"]:
        print(f"\n📝 Extracted Text Documents:")
        print(f"   Count: {results['extracted_documents']['count']}")
        print(f"   Total Characters: {results['extracted_documents']['total_characters']:,}")
        if results["extracted_documents"]["character_distribution"]:
            dist = results["extracted_documents"]["character_distribution"]
            print(f"   Distribution:")
            print(f"   - Min: {dist['min']:,} characters")
            print(f"   - Max: {dist['max']:,} characters")
            print(f"   - Average: {dist['average']:,} characters")
    
    # Processed documents
    if results["processed_documents"]:
        print(f"\n✨ Processed Text Documents:")
        print(f"   Count: {results['processed_documents']['count']}")
        print(f"   Total Characters: {results['processed_documents']['total_characters']:,}")
        if results["processed_documents"]["character_distribution"]:
            dist = results["processed_documents"]["character_distribution"]
            print(f"   Distribution:")
            print(f"   - Min: {dist['min']:,} characters")
            print(f"   - Max: {dist['max']:,} characters")
            print(f"   - Average: {dist['average']:,} characters")
    
    # Statistics
    if results["statistics"]:
        print(f"\n📈 Processing Statistics:")
        reduction = results["statistics"]["extraction_to_processing_reduction"]
        print(f"   Characters Removed: {reduction['characters_removed']:,}")
        print(f"   Reduction: {reduction['percentage']}%")
    
    # Duplicates
    print(f"\n🔍 Duplicate Detection:")
    if results["duplicates"]:
        print(f"   Found {len(results['duplicates'])} duplicate groups:")
        for i, group in enumerate(results["duplicates"], 1):
            print(f"   Group {i}: {', '.join(group)}")
    else:
        print(f"   ✅ No duplicates found")
    
    # Formats
    print(f"\n📋 Formats Present:")
    formats = set()
    if results["raw_documents"]["count"] > 0:
        formats.add("PDF")
    if results["extracted_documents"]["count"] > 0:
        formats.add("TXT (extracted)")
    if results["processed_documents"]["count"] > 0:
        formats.add("TXT (processed)")
    for fmt in formats:
        print(f"   - {fmt}")
    
    print("\n" + "="*60)
    print("✅ Quantitative analysis complete!")
    print("="*60 + "\n")

def main():
    """Run quantitative analysis"""
    
    project_root = get_project_root()
    data_dir = project_root / "data"
    
    print("🔍 Starting quantitative analysis of compliance corpus...")
    print(f"📂 Data directory: {data_dir}\n")
    
    # Run analysis
    results = analyze_documents(data_dir)
    
    # Print report
    print_analysis_report(results)
    
    # Save results
    output_dir = project_root / "analysis"
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "quantitative_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"💾 Results saved to: {output_file}")

if __name__ == "__main__":
    main()
