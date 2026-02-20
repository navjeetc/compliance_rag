# Data Documentation

This document records the data sourcing, extraction, and processing pipeline for the Compliance RAG project.

## Data Sources

### Compliance PDFs

We use four compliance standard documents as our knowledge base:

1. **CJIS Security Policy v6.0** (`cjis.pdf`)
   - Source: Criminal Justice Information Services
   - Size: 4.6 MB
   - Content: Security policy for criminal justice information systems

2. **SOC 2 Compliance** (`SOC2.pdf`)
   - Source: Service Organization Control 2
   - Size: 1.3 MB
   - Content: SOC 2 compliance framework and requirements

3. **NIST SP 800-53 Rev 5.1** (`nist.pdf`)
   - Source: National Institute of Standards and Technology
   - Size: 3.1 MB
   - Content: Security and Privacy Controls for Information Systems

4. **HIPAA Simplification** (`hipaa.pdf`)
   - Source: Health Insurance Portability and Accountability Act
   - Size: 829 KB
   - Content: HIPAA administrative simplification regulations

**Google Drive Location:**  
All PDFs are available in this public folder:  
https://drive.google.com/drive/folders/1GQM54O5lpZLKA6zmkiUotpd0HESRQ6_U

## Data Processing Pipeline

### Extract → Preprocess → Store

Our three-stage pipeline processes the compliance PDFs into clean, structured text ready for indexing.

### Stage 1: Extract

**Script:** `scripts/extract_pdf_text.py`

**Process:**
- Used PyPDFToDocument from Haystack to extract raw text from PDFs
- Extracted text saved to `data/extracted/`
- Created metadata JSON files for each document

**Results:**
- Total extracted: 3,296,251 characters
- SOC2: 391,181 chars
- CJIS: 1,152,334 chars
- HIPAA: 470,012 chars
- NIST: 1,282,724 chars

**Metadata Captured:**
- Document title
- Document type (compliance_standard)
- Source organization
- Google Drive URL
- Extraction date
- Text length
- Original filename

### Stage 2: Preprocess

**Script:** `scripts/preprocess_text.py`

**Cleaning Steps Applied:**
1. **Remove page artifacts:** Page numbers, headers, footers
2. **Normalize whitespace:** Remove excessive spaces and blank lines
3. **Clean TOC artifacts:** Remove dot leaders and page references
4. **Normalize section headers:** Consistent spacing after section numbers
5. **Clean special characters:** Fix encoding issues, normalize quotes/dashes
6. **Preserve structure:** Maintain paragraph breaks and document hierarchy

**Results:**
- Total processed: 3,170,530 characters
- Total reduction: 125,721 characters (3.81%)
- SOC2: 0.06% reduction (minimal artifacts)
- CJIS: 4.68% reduction
- HIPAA: 7.46% reduction
- NIST: 2.85% reduction

**What Was Removed:**
- Page numbers and pagination artifacts
- Excessive whitespace and empty lines
- Table of contents dot leaders (e.g., "Introduction ........ 5")
- Header/footer boilerplate
- Special characters and encoding artifacts

**What Was Preserved:**
- Document structure and hierarchy
- Section numbering and headers
- Paragraph breaks
- Technical content and terminology
- Tables and lists

### Stage 3: Store

**Location:** `data/processed/`

**Files Created:**
- `{document}.txt` - Cleaned text content
- `{document}_metadata.json` - Enhanced metadata with processing stats

**Metadata Enrichment:**
- Added preprocessing date
- Added processing statistics (reduction %, character counts)
- Preserved original extraction metadata
- Added processed filename reference

## Data Quality Notes

### Extraction Quality
- ✅ All 4 PDFs extracted successfully
- ✅ Text structure preserved (sections, paragraphs, lists)
- ✅ No major extraction errors
- ⚠️ Some formatting artifacts from PDF conversion (handled in preprocessing)

### Preprocessing Quality
- ✅ Page numbers and headers successfully removed
- ✅ Whitespace normalized without losing structure
- ✅ Special characters cleaned up
- ✅ Document hierarchy preserved
- ⚠️ Some table formatting may be simplified (acceptable for RAG)

### Content Coverage
- **CJIS:** Comprehensive security policy with technical requirements
- **SOC 2:** Framework and audit criteria
- **NIST:** Detailed security controls catalog
- **HIPAA:** Administrative and privacy regulations

### Filtering Decisions

**What We Kept:**
- All regulatory text and requirements
- Section headers and numbering
- Technical specifications
- Definitions and terminology
- Compliance criteria

**What We Filtered:**
- Page numbers
- Document headers/footers
- Table of contents page references
- Excessive whitespace
- PDF encoding artifacts

**Why:**
- Focus on substantive content for RAG retrieval
- Reduce noise in embeddings
- Improve chunk quality
- Maintain document structure for context

## Next Steps

1. ✅ Extract text from PDFs
2. ✅ Preprocess and clean text
3. ✅ Store processed data
4. 🔄 Index documents in Qdrant vector database
5. 🔄 Test RAG retrieval quality
6. 🔄 Evaluate and iterate on chunking strategy

## File Structure

```
data/
├── README.md                    # This file
├── PDF_SOURCES.md              # Google Drive links to PDFs
├── raw/                        # Original PDFs (gitignored)
│   ├── cjis.pdf
│   ├── SOC2.pdf
│   ├── nist.pdf
│   └── hipaa.pdf
├── extracted/                  # Raw extracted text
│   ├── cjis.txt
│   ├── cjis_metadata.json
│   ├── SOC2.txt
│   ├── SOC2_metadata.json
│   ├── nist.txt
│   ├── nist_metadata.json
│   ├── hipaa.txt
│   └── hipaa_metadata.json
└── processed/                  # Cleaned, preprocessed text
    ├── cjis.txt
    ├── cjis_metadata.json
    ├── SOC2.txt
    ├── SOC2_metadata.json
    ├── nist.txt
    ├── nist_metadata.json
    ├── hipaa.txt
    └── hipaa_metadata.json
```

## Reproducibility

To reproduce the data processing:

```bash
# 1. Download PDFs from Google Drive to data/raw/
# (See PDF_SOURCES.md for links)

# 2. Extract text from PDFs
python scripts/extract_pdf_text.py

# 3. Preprocess extracted text
python scripts/preprocess_text.py

# 4. Verify output in data/processed/
```

## Data Checkpoint

The processed data in `data/processed/` serves as a checkpoint before indexing. This allows us to:
- Re-index with different chunking strategies without re-processing
- Experiment with different embedding models
- Iterate on RAG pipeline without re-extracting from PDFs
- Maintain a clean, version-controlled preprocessing pipeline
