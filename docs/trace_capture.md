# RAG Session Trace Capture

## Overview

The trace capture system records RAG sessions for evaluation and debugging. Each session captures:
- Questions asked
- Retrieved chunks (with scores and metadata)
- Generated answers (in full RAG mode)
- Query timing and metadata

Traces are saved as JSON files in `traces/session_YYYYMMDD_HHMMSS.json` format.

## Usage

### Full RAG Mode (Retrieve + Generate)

```bash
# Default mode - captures retrieval and generation
python scripts/06_capture_traces.py

# With specific model
python scripts/06_capture_traces.py --model gemini-2.5-flash-lite

# Custom number of chunks
python scripts/06_capture_traces.py --top-k 10
```

### Retrieve-Only Mode

Use retrieve-only mode to inspect what chunks are being retrieved **without LLM generation**. This helps isolate retrieval issues from generation issues.

```bash
# Retrieve-only mode
python scripts/06_capture_traces.py --retrieve-only

# With more chunks
python scripts/06_capture_traces.py --retrieve-only --top-k 10
```

### Custom Output Directory

```bash
# Save traces to custom directory
python scripts/06_capture_traces.py --output-dir my_evaluation/
```

## Interactive Session

Once started, you can:

1. **Ask questions** - Type your compliance questions
2. **Review results** - See retrieved chunks and generated answers
3. **Exit** - Type `quit`, `exit`, or `q` to save traces and exit

Example session:
```
🔍 Your question: What are the password requirements in CJIS?

⏳ Processing query 1...

📊 Retrieved 5 chunks (in 2.34s)
  [1] Score: 0.753 | data/processed/cjis.txt
      Preview: 5.4.1 Password Requirements...
  [2] Score: 0.721 | data/processed/cjis.txt
      Preview: Passwords must be at least 8 characters...

💬 Answer (1234 chars):
According to CJIS Security Policy Section 5.4.1, password requirements include...

🔍 Your question: quit

✅ Session trace saved to: traces/session_20260220_190530.json
   2 queries captured
```

## Trace File Format

Traces are saved as JSON with the following structure:

```json
{
  "session_metadata": {
    "session_id": "20260220_190530",
    "started_at": "2026-02-20T19:05:30.123456",
    "ended_at": "2026-02-20T19:08:45.789012",
    "mode": "full_rag",
    "collection": "compliance_rag_v1",
    "embedding_model": "BAAI/bge-large-en-v1.5",
    "llm_model": "gemini-2.5-flash",
    "top_k": 5,
    "total_queries": 2,
    "session_duration_seconds": 195.67
  },
  "queries": [
    {
      "query_id": 1,
      "timestamp": "2026-02-20T19:05:32.456789",
      "question": "What are the password requirements in CJIS?",
      "retrieved_contexts": [
        {
          "rank": 1,
          "score": 0.753,
          "content": "5.4.1 Password Requirements...",
          "metadata": {
            "file_path": "data/processed/cjis.txt",
            "source_id": "cjis",
            "split_id": "cjis_chunk_42",
            "split_idx_start": 12500
          }
        }
      ],
      "generated_answer": "According to CJIS Security Policy...",
      "num_contexts_retrieved": 5,
      "query_time_seconds": 2.34
    }
  ]
}
```

## Evaluation Workflow

### 1. Capture Traces

Run interactive sessions and ask diverse questions:

```bash
python scripts/06_capture_traces.py
```

### 2. Review Traces

For each query in the trace file, assess:

- ✅ **Answer Correctness**: Is the generated answer accurate?
- ✅ **Context Quality**: Were the right chunks retrieved?
- ✅ **Completeness**: Were all relevant chunks included?
- ✅ **Citations**: Are citations accurate and specific?

### 3. Document Findings

Create assessment notes in `traces/assessment_notes.md`:

```markdown
# Session: 20260220_190530

## Query 1: Password requirements in CJIS

**Assessment:**
- ✅ Answer is correct
- ✅ Right context was retrieved
- ✅ All relevant chunks included
- ✅ Citations are accurate (Section 5.4.1)

**Notes:** Excellent retrieval and generation. All password requirements covered.

## Query 2: Audit log retention

**Assessment:**
- ❌ Answer is incomplete
- ⚠️ Missing NIST SP 800-53 AU-11 control
- ✅ CJIS requirements correct
- ⚠️ Should retrieve from multiple frameworks

**Notes:** Need to improve cross-framework retrieval for comprehensive answers.
```

## Use Cases

### Debugging Retrieval Issues

Use retrieve-only mode to see exactly what chunks are being retrieved:

```bash
python scripts/06_capture_traces.py --retrieve-only
```

This helps answer:
- Are the right documents being retrieved?
- Are chunk scores reasonable?
- Is the content relevant to the question?

### Testing Different Configurations

Compare retrieval quality with different top-k values:

```bash
# Test with 5 chunks
python scripts/06_capture_traces.py --top-k 5 --output-dir traces/top5/

# Test with 10 chunks
python scripts/06_capture_traces.py --top-k 10 --output-dir traces/top10/
```

### Building Evaluation Dataset

Capture traces from real usage to build an evaluation dataset:

1. Run multiple sessions with diverse questions
2. Review and assess each query
3. Create golden answers for high-quality questions
4. Use traces for regression testing

## Best Practices

### Question Diversity

Ask questions across different:
- **Frameworks**: CJIS, NIST, SOC 2, HIPAA
- **Topics**: Access control, encryption, audit logging, etc.
- **Difficulty**: Simple lookups, complex comparisons, cross-framework queries

### Assessment Criteria

For each query, evaluate:

1. **Retrieval Quality**
   - Were relevant chunks retrieved?
   - Were irrelevant chunks excluded?
   - Are scores reasonable (>0.7 for good matches)?

2. **Answer Quality** (full RAG mode)
   - Is the answer factually correct?
   - Are citations specific and accurate?
   - Is the answer complete?
   - Does it avoid hallucination?

3. **Performance**
   - Is query time acceptable (<5s ideal)?
   - Are there any errors or warnings?

### Trace Organization

Organize traces by purpose:

```
traces/
├── baseline/              # Initial system performance
├── after_tuning/          # After retrieval tuning
├── edge_cases/            # Difficult or edge case queries
└── production_samples/    # Real user queries
```

## Troubleshooting

### No Chunks Retrieved

If no chunks are retrieved:
- Check collection name is correct
- Verify Qdrant connection
- Ensure documents are indexed
- Try simpler, more direct questions

### Low Relevance Scores

If all scores are <0.5:
- Question may be too vague or broad
- Embedding model mismatch (must match indexing)
- Content may not exist in corpus

### Generation Errors

If LLM generation fails:
- Check API key is valid
- Verify model name is correct
- Try retrieve-only mode to isolate issue
- Check rate limits

## Related Scripts

- `scripts/05_interactive_rag.py` - Interactive RAG without trace capture
- `scripts/04_test_rag_system.py` - Automated testing with predefined queries
- `test_retrieval.py` - Retrieval-only testing

## Next Steps

After capturing traces:

1. **Analyze patterns** - What types of questions work well? Which fail?
2. **Identify gaps** - What content is missing from the corpus?
3. **Tune retrieval** - Adjust top-k, try different embedding models
4. **Improve prompts** - Refine system prompts based on failures
5. **Build evaluation set** - Create golden Q&A pairs from good traces
