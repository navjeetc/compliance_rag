#!/usr/bin/env python3
"""
End-to-End Pipeline Test
========================

Comprehensive test suite for the Extract → Preprocess → Store pipeline.
Validates data integrity, processing quality, and metadata consistency.

Usage:
    python test_pipeline.py
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple


# Project paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
EXTRACTED_DIR = PROJECT_ROOT / "data" / "extracted"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Expected documents
EXPECTED_DOCS = ["cjis", "SOC2", "nist", "hipaa"]


class TestResult:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
    
    def add_pass(self, test_name: str, message: str = ""):
        self.passed.append((test_name, message))
    
    def add_fail(self, test_name: str, message: str):
        self.failed.append((test_name, message))
    
    def add_warning(self, test_name: str, message: str):
        self.warnings.append((test_name, message))
    
    def print_summary(self):
        total = len(self.passed) + len(self.failed)
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {len(self.passed)}/{total}")
        print(f"❌ Failed: {len(self.failed)}/{total}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        
        if self.failed:
            print("\n❌ Failed Tests:")
            for test_name, message in self.failed:
                print(f"   - {test_name}: {message}")
        
        if self.warnings:
            print("\n⚠️  Warnings:")
            for test_name, message in self.warnings:
                print(f"   - {test_name}: {message}")
        
        print("\n" + "=" * 60)
        if len(self.failed) == 0:
            print("🎉 ALL TESTS PASSED!")
        else:
            print("💥 SOME TESTS FAILED")
        print("=" * 60)
        
        return len(self.failed) == 0


def test_directory_structure(results: TestResult):
    """Test that all required directories exist."""
    print("\n🧪 Testing Directory Structure...")
    
    directories = [
        ("data/raw", RAW_DATA_DIR),
        ("data/extracted", EXTRACTED_DIR),
        ("data/processed", PROCESSED_DIR),
    ]
    
    for name, path in directories:
        if path.exists() and path.is_dir():
            results.add_pass(f"Directory: {name}", f"Exists at {path}")
            print(f"   ✅ {name} exists")
        else:
            results.add_fail(f"Directory: {name}", f"Missing at {path}")
            print(f"   ❌ {name} missing")


def test_pdf_files(results: TestResult):
    """Test that all PDF files exist in raw directory."""
    print("\n🧪 Testing PDF Files...")
    
    for doc in EXPECTED_DOCS:
        pdf_file = RAW_DATA_DIR / f"{doc}.pdf"
        if pdf_file.exists():
            size_mb = pdf_file.stat().st_size / (1024 * 1024)
            results.add_pass(f"PDF: {doc}.pdf", f"Size: {size_mb:.2f} MB")
            print(f"   ✅ {doc}.pdf ({size_mb:.2f} MB)")
        else:
            results.add_fail(f"PDF: {doc}.pdf", "File not found")
            print(f"   ❌ {doc}.pdf missing")


def test_extracted_files(results: TestResult) -> Dict[str, int]:
    """Test that all extracted files exist and have content."""
    print("\n🧪 Testing Extracted Files...")
    
    extracted_sizes = {}
    
    for doc in EXPECTED_DOCS:
        # Test text file
        text_file = EXTRACTED_DIR / f"{doc}.txt"
        if text_file.exists():
            content = text_file.read_text(encoding='utf-8')
            char_count = len(content)
            extracted_sizes[doc] = char_count
            
            if char_count > 0:
                results.add_pass(f"Extracted: {doc}.txt", f"{char_count:,} characters")
                print(f"   ✅ {doc}.txt ({char_count:,} chars)")
            else:
                results.add_fail(f"Extracted: {doc}.txt", "File is empty")
                print(f"   ❌ {doc}.txt is empty")
        else:
            results.add_fail(f"Extracted: {doc}.txt", "File not found")
            print(f"   ❌ {doc}.txt missing")
        
        # Test metadata file
        metadata_file = EXTRACTED_DIR / f"{doc}_metadata.json"
        if metadata_file.exists():
            try:
                metadata = json.loads(metadata_file.read_text(encoding='utf-8'))
                required_fields = ["title", "type", "source", "extraction_date", "text_length"]
                missing_fields = [f for f in required_fields if f not in metadata]
                
                if not missing_fields:
                    results.add_pass(f"Metadata: {doc}_metadata.json", "All required fields present")
                    print(f"   ✅ {doc}_metadata.json")
                else:
                    results.add_fail(f"Metadata: {doc}_metadata.json", f"Missing fields: {missing_fields}")
                    print(f"   ❌ {doc}_metadata.json missing fields: {missing_fields}")
            except json.JSONDecodeError as e:
                results.add_fail(f"Metadata: {doc}_metadata.json", f"Invalid JSON: {e}")
                print(f"   ❌ {doc}_metadata.json invalid JSON")
        else:
            results.add_fail(f"Metadata: {doc}_metadata.json", "File not found")
            print(f"   ❌ {doc}_metadata.json missing")
    
    return extracted_sizes


def test_processed_files(results: TestResult, extracted_sizes: Dict[str, int]):
    """Test that all processed files exist and preprocessing worked."""
    print("\n🧪 Testing Processed Files...")
    
    for doc in EXPECTED_DOCS:
        # Test text file
        text_file = PROCESSED_DIR / f"{doc}.txt"
        if text_file.exists():
            content = text_file.read_text(encoding='utf-8')
            char_count = len(content)
            
            if char_count > 0:
                # Check that preprocessing reduced size (or kept it similar)
                if doc in extracted_sizes:
                    original = extracted_sizes[doc]
                    reduction = original - char_count
                    reduction_pct = (reduction / original * 100) if original > 0 else 0
                    
                    results.add_pass(f"Processed: {doc}.txt", f"{char_count:,} chars ({reduction_pct:.2f}% reduction)")
                    print(f"   ✅ {doc}.txt ({char_count:,} chars, {reduction_pct:.2f}% reduction)")
                    
                    # Warning if reduction is too high (might indicate over-processing)
                    if reduction_pct > 20:
                        results.add_warning(f"Processed: {doc}.txt", f"High reduction: {reduction_pct:.2f}%")
                else:
                    results.add_pass(f"Processed: {doc}.txt", f"{char_count:,} characters")
                    print(f"   ✅ {doc}.txt ({char_count:,} chars)")
            else:
                results.add_fail(f"Processed: {doc}.txt", "File is empty")
                print(f"   ❌ {doc}.txt is empty")
        else:
            results.add_fail(f"Processed: {doc}.txt", "File not found")
            print(f"   ❌ {doc}.txt missing")
        
        # Test metadata file
        metadata_file = PROCESSED_DIR / f"{doc}_metadata.json"
        if metadata_file.exists():
            try:
                metadata = json.loads(metadata_file.read_text(encoding='utf-8'))
                required_fields = ["title", "type", "source", "extraction_date", "preprocessing_date", "preprocessing_stats"]
                missing_fields = [f for f in required_fields if f not in metadata]
                
                if not missing_fields:
                    results.add_pass(f"Metadata: {doc}_metadata.json", "All required fields present")
                    print(f"   ✅ {doc}_metadata.json")
                else:
                    results.add_fail(f"Metadata: {doc}_metadata.json", f"Missing fields: {missing_fields}")
                    print(f"   ❌ {doc}_metadata.json missing fields: {missing_fields}")
            except json.JSONDecodeError as e:
                results.add_fail(f"Metadata: {doc}_metadata.json", f"Invalid JSON: {e}")
                print(f"   ❌ {doc}_metadata.json invalid JSON")
        else:
            results.add_fail(f"Metadata: {doc}_metadata.json", "File not found")
            print(f"   ❌ {doc}_metadata.json missing")


def test_content_quality(results: TestResult):
    """Test content quality of processed files."""
    print("\n🧪 Testing Content Quality...")
    
    for doc in EXPECTED_DOCS:
        text_file = PROCESSED_DIR / f"{doc}.txt"
        if not text_file.exists():
            continue
        
        content = text_file.read_text(encoding='utf-8')
        
        # Test 1: No excessive whitespace
        if '   ' not in content:  # No triple spaces
            results.add_pass(f"Quality: {doc} whitespace", "No excessive whitespace")
            print(f"   ✅ {doc}: No excessive whitespace")
        else:
            results.add_warning(f"Quality: {doc} whitespace", "Contains triple+ spaces")
            print(f"   ⚠️  {doc}: Contains excessive whitespace")
        
        # Test 2: No excessive newlines
        if '\n\n\n' not in content:  # No triple newlines
            results.add_pass(f"Quality: {doc} newlines", "No excessive newlines")
            print(f"   ✅ {doc}: No excessive newlines")
        else:
            results.add_warning(f"Quality: {doc} newlines", "Contains triple+ newlines")
            print(f"   ⚠️  {doc}: Contains excessive newlines")
        
        # Test 3: Has actual content (not just whitespace)
        if len(content.strip()) > 1000:
            results.add_pass(f"Quality: {doc} content", "Has substantial content")
            print(f"   ✅ {doc}: Has substantial content")
        else:
            results.add_fail(f"Quality: {doc} content", "Insufficient content")
            print(f"   ❌ {doc}: Insufficient content")


def test_documentation(results: TestResult):
    """Test that documentation files exist and have content."""
    print("\n🧪 Testing Documentation...")
    
    docs = [
        ("data/README.md", PROJECT_ROOT / "data" / "README.md"),
        ("data/PDF_SOURCES.md", PROJECT_ROOT / "data" / "PDF_SOURCES.md"),
        ("docs/scoping.md", PROJECT_ROOT / "docs" / "scoping.md"),
    ]
    
    for name, path in docs:
        if path.exists():
            content = path.read_text(encoding='utf-8')
            if len(content.strip()) > 100:
                results.add_pass(f"Documentation: {name}", f"{len(content)} characters")
                print(f"   ✅ {name} ({len(content)} chars)")
            else:
                results.add_warning(f"Documentation: {name}", "Very short content")
                print(f"   ⚠️  {name} is very short")
        else:
            results.add_fail(f"Documentation: {name}", "File not found")
            print(f"   ❌ {name} missing")


def run_all_tests():
    """Run all pipeline tests."""
    print("🚀 Starting Pipeline Tests")
    print("=" * 60)
    
    results = TestResult()
    
    # Run test suites
    test_directory_structure(results)
    test_pdf_files(results)
    extracted_sizes = test_extracted_files(results)
    test_processed_files(results, extracted_sizes)
    test_content_quality(results)
    test_documentation(results)
    
    # Print summary
    success = results.print_summary()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(run_all_tests())
