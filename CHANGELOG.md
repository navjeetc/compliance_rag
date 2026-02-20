# Changelog

All notable changes to the Compliance RAG project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - Data Preparation Pipeline (2026-02-20)

#### Project Structure
- Created complete project directory structure following RAG best practices
  - `data/raw/` - Original PDF documents (gitignored)
  - `data/extracted/` - Raw extracted text from PDFs
  - `data/processed/` - Cleaned and preprocessed text
  - `docs/` - Project documentation
  - `scripts/` - Data processing scripts
  - `analysis/` - Data quality analysis
  - `traces/` - Query trace logs

#### Data Sources
- Added 4 compliance standard PDFs (9.36 MB total):
  - CJIS Security Policy v6.0 (4.6 MB)
  - SOC 2 Compliance (1.3 MB)
  - NIST SP 800-53 Rev 5.1 (3.1 MB)
  - HIPAA Simplification (829 KB)
- Created `data/PDF_SOURCES.md` with Google Drive links for PDF sharing
- Uploaded all PDFs to public Google Drive folder

#### Extract → Preprocess → Store Pipeline

**Extraction (Stage 1)**
- Created `scripts/extract_pdf_text.py` for PDF text extraction
  - Uses PyPDFToDocument from Haystack
  - Extracts 3,296,251 characters from 4 compliance documents
  - Generates metadata JSON files for each document
  - Captures: title, type, source, URL, extraction date, text length

**Preprocessing (Stage 2)**
- Created `scripts/preprocess_text.py` for text cleaning and normalization
  - Removes page numbers, headers, and footers
  - Cleans table of contents artifacts and dot leaders
  - Normalizes whitespace and section headers
  - Fixes special characters and encoding issues
  - Reduces total text by 125,721 characters (3.81%) while preserving content
  - Individual reductions: SOC2 (0.06%), CJIS (4.68%), HIPAA (7.46%), NIST (2.85%)

**Storage (Stage 3)**
- Processed documents saved to `data/processed/` directory
- Enhanced metadata with preprocessing statistics
- Created checkpoint before indexing for pipeline iteration

#### Documentation
- Created comprehensive `data/README.md` documenting:
  - Data sources and Google Drive links
  - Complete Extract → Preprocess → Store pipeline
  - Processing statistics and results
  - Data quality notes and filtering decisions
  - File structure and reproducibility instructions
- Created `docs/scoping.md` with IDENTIFY/QUALIFY/DEFINE/SCOPE framework:
  - Problem: Manual compliance document search inefficiency
  - Users: Compliance analysts, security engineers, auditors
  - Capability: L2 Document QA with citation grounding
  - Success metrics: ≥85% accuracy, citation fidelity, <5s latency
  - Scope: 4 compliance frameworks with requirement lookup and citations

#### Configuration
- Updated Qdrant collection name from `mcp_phase1_baseline` to `compliance_rag_v1`
- Updated `.env.example` with compliance-specific configuration
- Copied `.env` from rag-accelerator-code project with credentials

#### Pipeline Scripts
- Modified `scripts/02_create_pipeline.py` to support PDF processing:
  - Added PyPDFToDocument converter
  - Updated FileTypeRouter to include `application/pdf` MIME type
  - Connected PDF converter to document processing pipeline
  - Updated pipeline documentation and validation

- Modified `scripts/03_run_indexing.py` to handle PDFs:
  - Added PDF file discovery in `data/raw/` directory
  - Updated file selection logic to prioritize PDFs in test mode
  - Added PDF file count reporting

#### Testing
- Created `test_pipeline.py` - Comprehensive end-to-end pipeline test
  - Tests directory structure (3 directories)
  - Validates PDF files (4 documents)
  - Checks extracted files (8 files: 4 text + 4 metadata)
  - Verifies processed files (8 files: 4 text + 4 metadata)
  - Validates content quality (whitespace, newlines, substantial content)
  - Confirms documentation completeness (3 documents)
  - **Result: 35/35 tests passed** with 3 minor warnings

- Created `test_pdf_extraction.py` - PDF text extraction verification
- Created `test_pdf_pipeline.py` - PDF discovery and pipeline component test

#### Dependencies
- Created `requirements.txt` with core dependencies:
  - haystack-ai>=2.16.1
  - qdrant-haystack>=9.2.0
  - fastembed-haystack>=1.5.0
  - pypdf>=3.17.4
  - fastembed>=0.7.1
  - python-dotenv>=1.1.1
  - tqdm>=4.67.1
  - pydantic>=2.11.7

#### Git & Version Control
- Initialized git repository
- Created `.gitignore` to exclude:
  - Environment variables (.env)
  - PDF files (data/raw/*.pdf)
  - Processed data (data/processed/*)
  - Python cache and virtual environments
- Created GitHub repository: `navjeetc/compliance_rag`
- Pushed initial commit to main branch
- Created feature branch: `feature/pdf-extraction-pipeline`

### Changed
- Renamed PDF files to simplified names:
  - `CJIS_Security_Policy_v6-0.pdf` → `cjis.pdf`
  - `SP_800-53_v5_1-derived-OSCAL.pdf` → `nist.pdf`
  - `hipaa-simplification-201303.pdf` → `hipaa.pdf`
  - `SOC2.pdf` → `SOC2.pdf` (unchanged)

### Statistics
- **Total Characters Extracted:** 3,296,251
- **Total Characters Processed:** 3,170,530
- **Total Reduction:** 125,721 characters (3.81%)
- **Files Created:** 26 (scripts, docs, data files, tests)
- **Git Commits:** 6 commits on feature branch
- **Tests Passed:** 35/35 (100%)

## [0.1.0] - 2026-02-20

### Added
- Initial project setup
- Basic directory structure
- Environment configuration template
- README placeholder files

---

## Future Releases

### Planned for Next Release
- Qdrant vector database indexing
- RAG query pipeline
- Citation extraction and grounding
- Evaluation framework
- Interactive query interface
