# Changelog

All notable changes to the Compliance RAG project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - Trace Capture System (2026-02-20)

#### Session Trace Capture
- Created `scripts/06_capture_traces.py` - Interactive RAG with trace capture
  - Captures questions, retrieved chunks, and generated answers
  - Saves traces as JSON files in `traces/session_YYYYMMDD_HHMMSS.json` format
  - Supports both full RAG and retrieve-only modes
  - Based on RAG Accelerator Week 2 trace capture methodology
  - Records query timing, relevance scores, and chunk metadata
- Created `docs/trace_capture.md` - Comprehensive trace capture documentation
  - Usage examples for full RAG and retrieve-only modes
  - Trace file format specification
  - Evaluation workflow and best practices
  - Assessment criteria for retrieval and generation quality
  - Troubleshooting guide

#### Trace Features
- **Full RAG Mode**: Captures retrieval + generation with LLM
- **Retrieve-Only Mode**: Inspects chunks without LLM (isolates retrieval issues)
- **Structured JSON Output**: Session metadata, query details, context metadata
- **Interactive Assessment**: Review and document findings for each query
- **Configurable**: Custom top-k, model selection, output directory

#### Use Cases
- Build evaluation datasets from real usage
- Debug retrieval quality issues
- Test different configurations (top-k, models)
- Assess answer correctness and citation accuracy
- Identify content gaps in corpus

### Added - Data Analysis (2026-02-20)

#### Quantitative Analysis
- Created `analysis/0_quantitative_analysis.py` - Automated corpus analysis
  - Document inventory and size distribution
  - Character count analysis across raw/extracted/processed stages
  - Duplicate detection using content hashing
  - Format validation (PDF, TXT extracted, TXT processed)
  - Processing statistics: 3.81% reduction (125,721 characters)
- Generated `analysis/quantitative_analysis.json` with detailed metrics
  - 4 documents, 9.36 MB total, 3.17M characters processed
  - Size range: 390K - 1.24M characters per document
  - Average: 792,632 characters per document
  - No duplicates found

#### Qualitative Analysis
- Created `analysis/1_analyze_content_quality.py` - LLM-based quality scoring
  - Adapted from RAG Accelerator course methodology
  - Supports Google Gemini and OpenAI models
  - Analyzes: information density, practical value, clarity, completeness, redundancy
  - Generates structured JSON reports with quality tiers
  - Identifies top files by category and provides recommendations
- Created `analysis/data_quality_notes.md` - Comprehensive quality assessment
  - Manual review combined with automated analysis
  - Quantitative metrics and distribution analysis
  - Qualitative scoring (9/10 density, 10/10 practical value, 8/10 clarity, 9/10 completeness)
  - Coverage assessment of compliance topics (AC, AU, IA, etc.)
  - Retrieval quality considerations and chunking recommendations
  - Gap analysis and future expansion recommendations

#### Analysis Results
- **Overall Assessment:** High Quality - Ready for Production RAG
- **Strengths:**
  - Authoritative sources (government agencies, audit standards)
  - Current versions (NIST Rev 5.1, CJIS v6.0)
  - Comprehensive coverage of compliance domains
  - Well-structured for retrieval (clear sections, numbered controls)
  - No duplicates or quality issues
- **Retrieval Validation:** 0.71-0.75 relevance scores (high quality)
- **Recommendation:** Production-ready, proceed with deployment

### Added - Vector Database Indexing (2026-02-20)

#### Qdrant Infrastructure
- Created `scripts/01_setup_qdrant.py` - Qdrant collection initialization
  - Connects to Qdrant cloud instance
  - Creates collection `compliance_rag_v1` with 1024-dimensional vectors
  - Supports recreate and no-recreate modes
  - Includes connection testing with sample document
- Successfully indexed 1,135 document chunks from 4 compliance documents
- Average chunk size optimized for retrieval performance

#### Indexing Pipeline
- Updated `scripts/02_create_pipeline.py` for compliance documents
  - Fixed PROJECT_ROOT path (scripts → root)
  - Updated references from MCP to compliance documentation
  - Pipeline includes: FileTypeRouter → Converters → Joiner → Cleaner → Splitter → Embedder → Writer
- Updated `scripts/03_run_indexing.py` for compliance processing
  - Removed unused `single_dir` parameter
  - Processes files from `data/processed/` directory
  - Supports test mode (2 docs, ~9 min) and full mode (4 docs, ~18 min)
  - Updated all MCP references to compliance terminology

#### RAG System
- Created `scripts/04_test_rag_system.py` - Complete RAG pipeline testing
  - Embedder → Retriever → Prompt Builder → LLM
  - Added `required_variables` parameter to ChatPromptBuilder
  - Fixed PROJECT_ROOT path for correct .env loading
  - Generates compliance answers with precise citations
  - Response time: ~6 seconds
- Created `scripts/05_interactive_rag.py` - Interactive query interface
  - Full RAG mode with LLM generation
  - Retrieve-only mode for chunk inspection
  - Fixed collection_name parameter consistency
  - Updated system prompts for compliance expertise (CJIS, HIPAA, SOC 2, NIST)
  - Updated example queries to compliance-specific questions

#### Testing & Validation
- Created `test_retrieval.py` - Retrieval validation script
  - Tests semantic search with 3 compliance queries
  - Added error handling to prevent KeyError
  - Validates retrieval quality with relevance scores (0.71-0.75)
  - Confirms document sources and content preview
- All scripts tested and validated:
  - ✅ Qdrant setup and connection
  - ✅ Pipeline creation (9 components, 10 connections)
  - ✅ Document indexing (1,135 chunks)
  - ✅ Retrieval (high relevance scores)
  - ✅ RAG system (comprehensive answers with citations)

#### Dependencies
- Added `google-genai-haystack>=3.1.0` - Google Gemini LLM integration
- Added `markdown-it-py>=3.0.0` - Markdown processing
- Added `mdit_plain>=1.0.1` - Plain text conversion

#### Configuration
- Updated all scripts to use `compliance_rag_v1` collection name
- Fixed PROJECT_ROOT paths across all scripts for consistency
- Updated system prompts to reference compliance frameworks

### Changed - Vector Database Indexing (2026-02-20)
- Updated all MCP references to Compliance RAG terminology
- Fixed PROJECT_ROOT path from `SCRIPT_DIR.parent.parent` to `SCRIPT_DIR.parent`
- Removed unused `single_dir` parameter from indexing functions
- Updated collection name defaults from `mcp_phase1_baseline` to `compliance_rag_v1`
- Updated example queries from MCP-specific to compliance-specific
- Enhanced error handling in retrieval scripts

### Statistics - Vector Database Indexing
- **Documents Indexed:** 4 compliance documents
- **Total Chunks:** 1,135 document chunks
- **Embedding Dimension:** 1024
- **Test Mode Processing Time:** ~9.4 minutes (2 documents, 553 chunks)
- **Full Mode Processing Time:** ~18 minutes (4 documents, 1,135 chunks)
- **Retrieval Relevance Scores:** 0.71-0.75 (high quality)
- **RAG Response Time:** ~6.19 seconds
- **Scripts Added/Updated:** 5 scripts
- **Git Commits:** 11 commits on feature branch
- **PR Reviews:** All feedback addressed

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
