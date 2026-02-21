# Week 1 Capstone Submission

## Student Name
Navjeet Chabbewal

## Project Title
Compliance RAG: Multi-Framework Security Control Query System

## Problem Statement
Compliance professionals spend hours manually searching through multiple security frameworks (CJIS, NIST SP 800-53, SOC 2, HIPAA) to answer specific control questions, leading to delayed audits and potential compliance gaps.

## Data Overview
- **Corpus size:** 4 documents, ~3.4M characters (~1,135 chunks after indexing)
- **Data sources:** Official government publications (CJIS FBI, NIST), AICPA standards (SOC 2), federal regulations (HIPAA)
- **Formats:** PDF → Plain text (.txt)
- **Domain:** Security compliance frameworks covering access control, encryption, audit logging, incident response, and technical safeguards

## Data Curation Summary
- **Extraction method:** Python PDF text extraction (PyPDF2) from official compliance framework PDFs
- **Preprocessing steps:** 
  - Removed page numbers, headers, footers, and PDF artifacts
  - Normalized whitespace and line breaks
  - Preserved section numbers, control IDs, and hierarchical structure
  - Added metadata (file_path, source_id, framework, version)
  - Validated character counts and section structure
- **Key decisions:** 
  - Excluded cover pages, TOC, revision history (no informational value)
  - Kept all control definitions, implementation guidance, and cross-references (core content)
  - Maintained control IDs (AU-*, AC-*, IA-*) for accurate citations
  - Achieved 3.8% size reduction while preserving all substantive content

## Pipeline Configuration
- **Vector database:** Qdrant (cloud-hosted)
- **Collection name:** compliance_rag_v1
- **Embedding model:** BAAI/bge-large-en-v1.5 (1024 dimensions)
- **Chunk strategy:** Character-based splitting (default Haystack DocumentSplitter, ~3000 chars/chunk)
- **LLM:** Google Gemini 2.5 Flash
- **Documents indexed:** 4 frameworks, 1,135 chunks
- **Top-K retrieval:** 5 chunks per query

## Trace Summary

Tested the system with 5 diverse queries covering framework-specific questions, cross-framework queries, and technical controls. The system demonstrates strong retrieval for framework-specific and cross-framework queries, with accurate answer generation and proper citations.

| Query | Retrieval | Answer | Notes |
|-------|-----------|--------|-------|
| Password requirements in CJIS | Good | Good | All 5 chunks from CJIS, comprehensive answer with citations |
| Audit log protection in NIST | Partial | Good | Retrieved AU-9 from CJIS instead of NIST; honest answer acknowledging limitation |
| Encryption for data at rest (HIPAA) | Good | Excellent | Correctly identified "addressable" vs "required" - critical nuance |
| Multi-factor authentication (cross-framework) | Excellent | Good | Successfully retrieved from CJIS, NIST, SOC 2; good synthesis |
| Incident response requirements | Excellent | Good | Strong cross-framework retrieval (IR-1, IR-4, IR-6 from NIST) |

## Observations

### What types of queries work well?
- **Framework-specific questions:** When asking about a specific framework (e.g., "in CJIS"), the system correctly filters to that framework with high precision
- **Cross-framework queries:** Multi-factor authentication and incident response queries successfully retrieved relevant content from multiple frameworks (CJIS, NIST, SOC 2)
- **Technical control questions:** Encryption, authentication, and logging queries retrieved relevant technical controls with good semantic matching
- **Nuanced requirements:** System correctly identified HIPAA encryption as "addressable" not "required" - a critical compliance distinction

### What types of queries struggle?
- **Missing control text:** NIST AU-9 (audit log protection) wasn't retrieved from NIST corpus, only from CJIS. This suggests either the NIST document doesn't contain AU-9 control text, or it's not being retrieved effectively
- **Overly specific retrievals:** Password requirements query focused heavily on mobile device PINs rather than general password requirements, suggesting the query may need expansion
- **Chunk boundary issues:** Some controls may be split across chunks, making complete retrieval difficult for complex multi-part controls

### Is the issue retrieval or generation?
**Primarily retrieval:**
- The LLM consistently generates accurate answers when the right context is retrieved
- The LLM correctly acknowledges when information is missing (Query 2: NIST AU-9 example)
- Generation quality is consistently good with proper framework citations and section references
- No hallucinations observed - the LLM stays grounded in retrieved context

**Retrieval issues identified:**
1. Some framework-specific controls not being retrieved from their source framework
2. Chunk boundaries may split related content (e.g., control definition + enhancements)
3. Query expansion might help (e.g., "audit log protection" → "AU-9" → "protection of audit information")
4. Default character-based chunking doesn't respect semantic boundaries

### What would you improve first?
**Week 2 priorities (in order):**

1. **Semantic chunking strategy** - Implement semantic chunking to keep related controls together (e.g., entire AU-9 control with all enhancements in one chunk). This addresses the chunk boundary issue observed in traces.

2. **Metadata enrichment** - Add control IDs (AU-9, IA-2, IR-4) and framework names as searchable metadata for better filtering and precision. This would help with framework-specific queries.

3. **Hybrid search** - Combine semantic search with keyword matching on control IDs and section numbers. This would improve retrieval of specific controls by their identifiers.

4. **Query expansion** - Map common compliance questions to framework-specific terminology (e.g., "audit logs" → "AU-9", "MFA" → "Advanced Authentication"). This would improve recall for domain-specific queries.

## Self-Assessment

| Criteria | Score (1-5) | Notes |
|----------|-------------|-------|
| Problem scoping clarity | 5 | Clear problem statement with specific user personas, well-defined capability level (L2: Document QA), thorough IDENTIFY/QUALIFY/DEFINE/SCOPE analysis |
| Data sourcing and curation | 5 | Official authoritative sources (FBI, NIST, AICPA, HHS), documented extraction and preprocessing, justified filtering decisions, validated quality metrics |
| Pipeline is functional | 5 | Fully functional pipeline: 1,135 chunks indexed, queries return results with proper citations, both retrieve-only and full RAG modes working |
| Trace quality and depth | 5 | 5 diverse traced queries with honest assessments, identified specific retrieval issues (NIST AU-9), distinguished retrieval vs generation problems, actionable improvement recommendations |
| Observations and analysis | 5 | Identified patterns (framework-specific vs cross-framework), root cause analysis (chunking boundaries), prioritized improvements for Week 2 with clear rationale |

**Overall assessment:** The baseline system demonstrates strong performance on framework-specific and cross-framework queries with accurate answer generation. The primary improvement area is chunking strategy to respect semantic boundaries of compliance controls. The system is ready for Week 2 optimization focused on semantic chunking, metadata enrichment, and hybrid search.
