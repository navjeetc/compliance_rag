# Week 1 Capstone: Problem Scoping

## IDENTIFY

### Problem Statement
Compliance professionals spend hours manually searching through multiple security frameworks (CJIS, NIST SP 800-53, SOC 2, HIPAA) to answer specific control questions, leading to delayed audits and potential compliance gaps.

### Who Experiences This Problem
- Security compliance officers
- IT auditors
- Security engineers implementing controls
- Risk management teams
- Organizations undergoing compliance audits

### Capability Level
**L2: Document QA**

This system provides precise answers to compliance questions by retrieving relevant sections from multiple security frameworks and generating accurate responses with specific citations. Users can ask questions like "What are the password requirements in CJIS?" and receive answers with exact control references.

---

## QUALIFY

### Is the corpus too large for a single context window?
**Yes.** The compliance corpus includes:
- CJIS Security Policy (v6.0): 1.5M+ characters
- NIST SP 800-53 Rev 5: 1.4M+ characters  
- SOC 2 Trust Services Criteria: 300K+ characters
- HIPAA Security Rule: 200K+ characters

Total: ~3.4M characters across 4 frameworks, far exceeding any LLM context window.

### Does semantic search add value over keyword matching?
**Yes.** Compliance questions are often conceptual:
- "How should audit logs be protected?" maps to AU-9 controls
- "What encryption is required for data at rest?" spans multiple frameworks
- "Password requirements" appears in different sections with varying terminology

Semantic search understands these conceptual relationships better than keyword matching.

### Does source attribution matter?
**Absolutely critical.** Compliance answers require:
- Exact framework citations (e.g., "CJIS Section 5.6.2.1")
- Specific control numbers (e.g., "NIST SP 800-53 AU-9")
- Version information for audit trails

Incorrect citations can lead to failed audits or compliance violations.

### Is the content domain-specific or proprietary?
**Yes.** Security compliance frameworks use specialized terminology:
- Technical controls (AU, AC, IA, SC families)
- Compliance-specific concepts (CJI, ePHI, PII)
- Framework-specific requirements and enhancements

General-purpose models lack this specialized knowledge.

---

## DEFINE

### Success Targets

#### Accuracy
**Target: 70%** of answers should be factually correct with proper citations.

For Week 1 baseline, this means:
- Correct framework identified
- Relevant control sections retrieved
- Citations are accurate (section numbers, control IDs)
- No hallucinated requirements

#### Coverage
**Target: 60%** of expected compliance questions should be answerable.

Expected question types:
- Control requirements ("What are the password requirements?")
- Implementation guidance ("How should audit logs be protected?")
- Framework comparisons ("What encryption standards apply?")
- Specific technical controls (authentication, encryption, logging)

#### Latency
**Target: <5 seconds** per query for acceptable user experience.

Breakdown:
- Embedding: <1s
- Retrieval: <1s
- LLM generation: <3s

---

## SCOPE

### Corpus Size
**4 documents, ~3.4M characters**

| Framework | Size | Format |
|-----------|------|--------|
| CJIS Security Policy v6.0 | 1.5M chars | PDF → TXT |
| NIST SP 800-53 Rev 5 | 1.4M chars | PDF → TXT |
| SOC 2 TSC | 300K chars | PDF → TXT |
| HIPAA Security Rule | 200K chars | PDF → TXT |

### Document Formats
- **Source:** PDF documents (official compliance frameworks)
- **Extracted:** Plain text (PDF text extraction)
- **Processed:** Cleaned text (removed headers, footers, page numbers)

### Data Change Frequency
**Infrequent updates** (annually or less):
- CJIS: Annual updates (currently v6.0, Dec 2024)
- NIST SP 800-53: Major revisions every 3-5 years (Rev 5, Sept 2020)
- SOC 2: Stable criteria with minor clarifications
- HIPAA: Regulatory changes are rare

This makes the corpus suitable for static indexing with periodic re-indexing on framework updates.

### Data Quality
**High quality, authoritative sources:**
- Official government publications (CJIS, NIST)
- AICPA standards (SOC 2)
- Federal regulations (HIPAA)

**Challenges:**
- PDF extraction artifacts (page breaks, formatting)
- Inconsistent structure across frameworks
- Dense technical language
- Cross-references between sections

### Data Ownership
**Public domain and regulatory:**
- CJIS: FBI CJIS Division (public)
- NIST: National Institute of Standards and Technology (public)
- SOC 2: AICPA (publicly available criteria)
- HIPAA: HHS Office for Civil Rights (public regulation)

All frameworks are publicly accessible for compliance purposes.

---

## Week 1 Baseline Scope

For this initial implementation:
- **All 4 frameworks indexed** (~3.4M characters, 1,135 chunks)
- **Default chunking strategy** (character-based splitting)
- **Single embedding model** (BAAI/bge-large-en-v1.5, 1024-dim)
- **Qdrant vector database** (cloud-hosted)
- **Google Gemini 2.5 Flash** for generation
- **Top-K retrieval** (5 chunks per query)

Future improvements (Weeks 2-6):
- Optimized chunking strategies (semantic, hierarchical)
- Hybrid search (semantic + keyword)
- Query classification and routing
- Multi-framework answer synthesis
- Evaluation dataset and metrics
