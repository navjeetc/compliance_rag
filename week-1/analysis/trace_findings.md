# Trace Analysis Findings - Compliance RAG Baseline

**Analysis Date:** 2026-02-20
**Analyst:** Navjeet Chabbewal
**Sessions Analyzed:** 4 JSON trace files + 1 annotated markdown trace
**Total Queries:** 7 unique queries (some repeated across sessions for reproducibility)

---

## Sessions Covered

| Session File | Mode | Queries | Notes |
|---|---|---|---|
| `example_session_20260220_193006.json` | full_rag | 1 | Single-query baseline |
| `session_20260220_193219.json` | full_rag | 2 | Repeated password + NIST audit query |
| `session_20260220_194619.json` | full_rag | 1 | Encryption at rest (no framework specified) |
| `session_20260220_194847.json` | full_rag | 3 | NIST audit + encryption + third query |
| `week-1/traces/trace.md` | full_rag | 5 | Annotated Week 1 submission traces |

**Configuration across all sessions:**
- Embedding model: `BAAI/bge-large-en-v1.5` (1024 dims, FastEmbed)
- LLM: `gemini-2.5-flash`
- Top-K: 5
- Collection: `compliance_rag_v1`

---

## Queries Tested

| # | Query | Type | Result |
|---|---|---|---|
| Q1 | What are the password requirements in CJIS? | Framework-specific | Partial |
| Q2 | How should audit logs be protected according to NIST? | Framework-specific | Problematic |
| Q3 | What encryption is required for data at rest in HIPAA? | Framework-specific (with HIPAA) | Good |
| Q4 | What encryption is required for data at rest? | Cross-framework (no filter) | Different result from Q3 |
| Q5 | What are the multi-factor authentication requirements across frameworks? | Cross-framework | Excellent |
| Q6 | What are the incident response requirements for security incidents? | Cross-framework | Excellent |
| Q7 | *(Third query in session_194847 — content not captured in review)* | — | — |

---

## What Works Well

### 1. Generation quality: grounded, honest, no hallucinations

Across all sessions the LLM never fabricated content. When the right chunks were retrieved, answers were accurate and well-cited with section numbers and control IDs (e.g., "§ 164.312", "AU-9", "Section 5.4.3"). When context was missing, the model said so explicitly rather than guessing.

**Key example — Q2 (NIST audit log protection):**
The model correctly stated: *"The concept of protecting audit information from unauthorized access, modification, and deletion is present in the `cjis.txt` document under AU-9, but this is from the CJIS Security Policy, not the NIST documents provided."*
This is the correct behavior: honest acknowledgment of the gap.

**Key example — Q3 (HIPAA encryption):**
The model correctly identified that HIPAA encryption is **"addressable"** (a risk-based decision), not a hard "required" safeguard. This is a critical compliance distinction that a naive model would likely miss.

---

### 2. Cross-framework retrieval works for broad queries

Queries that don't anchor to a specific framework successfully retrieve relevant chunks from multiple sources.

**Q5 (MFA across frameworks)** — retrieved from 3 frameworks:
- `cjis.txt` (score 0.7234) — Section 5.6.2.2 Advanced Authentication
- `nist.txt` (score 0.7012) — IA-2(1) Multi-Factor Authentication to Privileged Accounts
- `nist.txt` (score 0.6834) — IA-2(2) Non-Privileged Accounts
- `soc2.txt` (score 0.6723) — CC6.1 logical access security

**Q6 (Incident response)** — retrieved IR-1, IR-4, IR-6 from NIST, Section 5.4.3 from CJIS, CC7.3 from SOC 2. All directly relevant.

The semantic model is doing its job for this query type.

---

### 3. Relevance scores are in a healthy range

Top-chunk scores consistently in the 0.71–0.74 range. Scores below 0.65 (ranks 3–5 in several queries) are where noise starts appearing, but the top 2 chunks are nearly always relevant.

---

## Issues Found

### Issue 1: NIST AU-9 is sourced from CJIS, not NIST (HIGH PRIORITY)

**Affected queries:** Q2 — "How should audit logs be protected according to NIST?"
**Observed in:** `session_20260220_193219.json` (query_id 2), `session_20260220_194847.json` (query_id 1)
**Consistent across sessions:** Yes — identical result both times (top chunk score 0.73989207 from `cjis.txt` split_id 56, offset 159241)

**What happens:**
The top-ranked chunk (score 0.739) comes from `cjis.txt`, not `nist.txt`. The CJIS policy document embeds the full NIST SP 800-53 AU-9 control text verbatim within its own policy body. This creates a situation where the CJIS document semantically outscores the NIST source for a NIST-specific question.

**Chunk content (cjis.txt, split_id 56):**
```
AU-9 PROTECTION OF AUDIT INFORMATION
[Existing] [Priority 2]
Control:
a. Protect audit information and audit logging tools from unauthorized access, modification,
and deletion; and
b. Alert organizational personnel...
```
This text appears in CJIS but is labeled as a NIST control. The system has no way to know the user means "find this in the NIST source document" versus "find where this control is defined."

**Root cause:** No metadata-based source filtering. Purely semantic search cannot distinguish "AU-9 as cited in CJIS" from "AU-9 as defined in NIST."

---

### Issue 2: Password query retrieves mobile device appendix instead of base policy

**Affected queries:** Q1 — "What are the password requirements in CJIS?"
**Observed in:** All sessions containing Q1 (identical results each time)

**What happens:**
All 5 retrieved chunks come from the CJIS mobile device guidance appendix (Appendix G), not the base password policy Section 5.6.2.1. The answer covers mobile PINs, layered authentication, and BYOD scenarios rather than the foundational CJIS password requirements.

**Evidence — all retrieved chunks from the same region of cjis.txt:**

| Rank | Score | split_id | split_idx_start | Content preview |
|---|---|---|---|---|
| 1 | 0.7217 | 351 | 959,000 | "Minimum Password/Pin (Reference CJIS Security Policy Section 5.6.2.1)..." |
| 2 | 0.7149 | 342 | 936,067 | "Embedded passwords/login tied to device PIN..." |
| 3 | 0.6991 | 372 | 1,014,303 | "encrypting CJI is to prevent unauthorized access..." |
| 4 | 0.6990 | 343 | 938,646 | "Special Login attempt limit..." |
| 5 | 0.6937 | 368 | 1,003,572 | "CSC 12-5: Ensure that all service accounts have long passwords..." |

All offsets cluster between 936K–1,014K — the same appendix section. The actual Section 5.6.2.1 text (which is what the user is looking for) is at a different offset and scored lower than the appendix discussion of 5.6.2.1.

**Root cause:** The appendix has dense semantic overlap with the query terms ("password", "PIN", "CJIS", "authentication"). Word-based chunking with 400-word chunks doesn't distinguish the authoritative base control from supplementary guidance sections that reference it.

---

### Issue 3: NIST bibliography chunks appear in results

**Affected queries:** Q2 (audit log query)
**Observed in:** `session_20260220_193219.json` (query_id 2, rank 3), `session_20260220_194847.json` (query_id 1, rank 3)

**What happens:**
Rank 3 result (score 0.688) for the NIST audit log query is a NIST SP 800-53 references/bibliography page — a list of NIST SP 800-xxx publication citations. It contains compliance-domain vocabulary but zero substantive content for answering the question.

**Chunk content (nist.txt, split_id 426, offset 1,228,423):**
```
R, Schnitzer A, Sandlin K, Miller R, Scarfone KA (2014) Guide to
Attribute Based Access Control (ABAC) Definition and Considerations...
[SP 800-166] Cooper DA, Ferraiolo H...
[SP 800-167] Sedgewick A...
[SP 800-171] Ross RS...
```

This is the reference bibliography at the end of the NIST document. It scores 0.688 because it contains NIST publication names and compliance terminology — enough to place it above potentially better substantive chunks.

**Root cause:** Reference/bibliography sections were not filtered out during preprocessing. Their vocabulary (security, information systems, NIST) is similar enough to compliance queries to surface in results.

---

### Issue 4: Query phrasing sensitivity — HIPAA encryption result changes with phrasing

**Affected queries:** Q3 vs. Q4

**Q3** — "What encryption is required for data at rest **in HIPAA**?"
→ Top chunk from `hipaa.txt` (score 0.7156): § 164.312 addressable safeguard — correct answer

**Q4** — "What encryption is required for data at rest?"
→ Top chunk from `cjis.txt` (score 0.7264): CJIS SC-28 cryptographic protection
→ Rank 2 from `nist.txt` (score 0.7191): NIST SC-28
→ HIPAA chunk does not appear in top 5

Adding "in HIPAA" to the query raises the HIPAA chunk to first place. Removing it causes the HIPAA requirement to disappear entirely from results.

**Root cause:** No query routing or framework-aware query expansion. The model treats all queries the same regardless of whether a framework is specified.

---

## Generation vs. Retrieval Diagnosis

| Layer | Assessment |
|---|---|
| **Generation** | Consistently good. Stays grounded, cites correctly, acknowledges gaps. No hallucinations observed across 7 queries. |
| **Retrieval — cross-framework broad queries** | Good. MFA and incident response queries retrieved relevant chunks from 3+ frameworks. |
| **Retrieval — framework-specific with explicit mention** | Mostly good, but vulnerable to cross-document contamination (Issue 1). |
| **Retrieval — framework-specific without metadata filter** | Unreliable (Issues 1 and 4). |
| **Chunking quality** | Needs improvement — appendix content outweighs base policy; reference sections indexed (Issues 2 and 3). |
| **Query routing / expansion** | Not implemented — single phrasing change produces qualitatively different results (Issue 4). |

**Conclusion: The bottleneck is retrieval, not generation.** The LLM performs well given whatever context it receives. Improving retrieval will directly improve end-to-end answer quality without requiring changes to the generation layer.

---

## Prioritized Improvements (for Week 2)

Listed in order of expected impact:

| Priority | Improvement | Issues Addressed | Effort |
|---|---|---|---|
| 1 | **Metadata filtering by framework** — add `framework` field to Qdrant payload; support `filter={"framework": "nist"}` on retrieval | Issues 1, 4 | Medium |
| 2 | **Semantic/structure-aware chunking** — split on control boundaries (e.g., "AC-2", "5.6.2.1") rather than word count | Issue 2 | Medium |
| 3 | **Preprocess out reference/TOC sections** — identify and exclude bibliography, table of contents, and revision history sections from indexing | Issue 3 | Low |
| 4 | **Query expansion / routing** — detect framework mentions in query and inject as metadata filter; map aliases ("audit logs" → "AU-9") | Issues 1, 4 | High |
| 5 | **Hybrid search** — combine semantic search with BM25/keyword on control IDs (AU-9, IA-2, etc.) | Issues 1, 2 | High |

---

## Appendix: Repeated Query Reproducibility

The NIST AU-9 retrieval failure (Issue 1) and the CJIS password appendix bias (Issue 2) both reproduced identically across multiple independent sessions. The same `split_id` values and scores appear in `session_20260220_193219.json` and `session_20260220_194847.json`. This confirms these are systematic retrieval issues, not one-off results.

| Issue | Sessions | Top chunk split_id | Top chunk score |
|---|---|---|---|
| NIST AU-9 from CJIS | 193219, 194847 | cjis.txt split_id 56 | 0.73989207 |
| Password appendix bias | 193006, 193219 | cjis.txt split_id 351 | 0.72174317 |
