#!/usr/bin/env python3
"""
Generate Example Traces with Predefined Questions
==================================================

Runs the trace capture system with predefined evaluation questions
to demonstrate the trace format and create example traces.

This is a non-interactive version for automated trace generation.

Usage:
    python scripts/07_generate_example_traces.py
    python scripts/07_generate_example_traces.py --retrieve-only
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from dotenv import load_dotenv

# Haystack imports
from haystack import Pipeline
from haystack.components.builders import ChatPromptBuilder
from haystack.dataclasses import ChatMessage

# FastEmbed imports
from haystack_integrations.components.embedders.fastembed import FastembedTextEmbedder
from haystack_integrations.components.retrievers.qdrant import QdrantEmbeddingRetriever

# Google Gemini imports
from haystack_integrations.components.generators.google_genai import GoogleGenAIChatGenerator

# Qdrant import
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore
from haystack.utils import Secret

# Get project root
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

# Example evaluation questions for compliance RAG
EXAMPLE_QUESTIONS = [
    {
        "question_id": 1,
        "question": "What are the password requirements in CJIS Security Policy?",
        "category": "authentication",
        "difficulty": "easy"
    },
    {
        "question_id": 2,
        "question": "How should audit logs be protected according to NIST SP 800-53?",
        "category": "audit_logging",
        "difficulty": "medium"
    },
    {
        "question_id": 3,
        "question": "What encryption is required for data at rest in HIPAA?",
        "category": "encryption",
        "difficulty": "easy"
    }
]


def create_retrieval_pipeline(collection_name: str = None, top_k: int = 5):
    """Create a retrieval-only pipeline."""
    load_dotenv(PROJECT_ROOT / ".env")
    
    collection_name = collection_name or os.getenv("QDRANT_COLLECTION_PHASE1", "compliance_rag_v1")
    fastembed_model = os.getenv("FASTEMBED_MODEL", "BAAI/bge-large-en-v1.5")
    
    print("Setting up retrieval pipeline...")
    print(f"  Collection: {collection_name}")
    print(f"  Top-K: {top_k}")
    
    document_store = QdrantDocumentStore(
        url=os.getenv("QDRANT_URL"),
        index=collection_name,
        api_key=Secret.from_env_var("QDRANT_API_KEY"),
        embedding_dim=int(os.getenv("EMBEDDING_DIMENSION", "1024")),
        recreate_index=False,
        return_embedding=True,
        wait_result_from_api=True
    )
    
    pipeline = Pipeline()
    text_embedder = FastembedTextEmbedder(model=fastembed_model, parallel=0, progress_bar=False)
    text_embedder.warm_up()
    pipeline.add_component("text_embedder", text_embedder)
    pipeline.add_component("retriever", QdrantEmbeddingRetriever(
        document_store=document_store,
        top_k=top_k
    ))
    pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
    
    print("✅ Pipeline ready\n")
    return pipeline


def create_rag_pipeline(collection_name: str = None, llm_model: str = None, top_k: int = 5):
    """Create full RAG pipeline."""
    load_dotenv(PROJECT_ROOT / ".env")
    
    collection_name = collection_name or os.getenv("QDRANT_COLLECTION_PHASE1", "compliance_rag_v1")
    fastembed_model = os.getenv("FASTEMBED_MODEL", "BAAI/bge-large-en-v1.5")
    llm_model = llm_model or os.getenv("LLM_MODEL", "gemini-2.5-flash")
    
    print("Setting up full RAG pipeline...")
    print(f"  LLM model: {llm_model}")
    print(f"  Collection: {collection_name}")
    print(f"  Top-K: {top_k}")
    
    document_store = QdrantDocumentStore(
        url=os.getenv("QDRANT_URL"),
        index=collection_name,
        api_key=Secret.from_env_var("QDRANT_API_KEY"),
        embedding_dim=int(os.getenv("EMBEDDING_DIMENSION", "1024")),
        recreate_index=False,
        return_embedding=True,
        wait_result_from_api=True
    )
    
    pipeline = Pipeline()
    text_embedder = FastembedTextEmbedder(model=fastembed_model, parallel=0, progress_bar=False)
    text_embedder.warm_up()
    pipeline.add_component("text_embedder", text_embedder)
    pipeline.add_component("retriever", QdrantEmbeddingRetriever(
        document_store=document_store,
        top_k=top_k
    ))
    
    template = [
        ChatMessage.from_system("""You are a compliance expert assistant. Answer questions about compliance requirements based ONLY on the provided context.

CRITICAL RULES:
1. Use ONLY information from the provided documents
2. Include specific citations (document name, section number)
3. If information is not in the context, say so clearly
4. Be precise and cite specific controls or requirements"""),
        ChatMessage.from_user("""Context documents:
{% for doc in documents %}
  Source: {{ doc.meta.file_path }}
  Content: {{ doc.content }}
{% endfor %}

Question: {{ question }}

Provide a detailed answer with specific citations.""")
    ]
    
    pipeline.add_component("prompt_builder", ChatPromptBuilder(
        template=template,
        required_variables=["documents", "question"]
    ))
    pipeline.add_component("llm", GoogleGenAIChatGenerator(
        model=llm_model
    ))
    
    pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
    pipeline.connect("retriever.documents", "prompt_builder.documents")
    pipeline.connect("prompt_builder.prompt", "llm.messages")
    
    print("✅ Pipeline ready\n")
    return pipeline, llm_model


def generate_traces(
    pipeline: Pipeline,
    questions: List[Dict],
    output_dir: Path,
    retrieve_only: bool = False,
    collection_name: str = "compliance_rag_v1",
    llm_model: str = None,
    top_k: int = 5
):
    """Generate traces for predefined questions."""
    
    session_start = datetime.now()
    session_id = session_start.strftime("%Y%m%d_%H%M%S")
    
    print("=" * 70)
    print(f"  Generating Example Traces - {'Retrieve-Only' if retrieve_only else 'Full RAG'}")
    print("=" * 70)
    print(f"  Questions: {len(questions)}")
    print(f"  Output: {output_dir}")
    print("=" * 70)
    print()
    
    traces = {
        "session_metadata": {
            "session_id": session_id,
            "started_at": session_start.isoformat(),
            "mode": "retrieve_only" if retrieve_only else "full_rag",
            "collection": collection_name,
            "embedding_model": os.getenv("FASTEMBED_MODEL", "BAAI/bge-large-en-v1.5"),
            "llm_model": llm_model if not retrieve_only else None,
            "top_k": top_k,
            "dataset": "example_questions"
        },
        "queries": []
    }
    
    for i, q in enumerate(questions, 1):
        question_text = q["question"]
        
        print(f"[{i}/{len(questions)}] {question_text}")
        start_time = time.time()
        
        # Query pipeline
        if retrieve_only:
            result = pipeline.run({"text_embedder": {"text": question_text}})
        else:
            result = pipeline.run({
                "text_embedder": {"text": question_text},
                "prompt_builder": {"question": question_text}
            })
        
        query_time = time.time() - start_time
        
        # Extract contexts
        # The pipeline result structure has documents directly in the result
        documents = []
        if "retriever" in result:
            documents = result["retriever"].get("documents", [])
        elif "documents" in result:
            documents = result.get("documents", [])
        contexts = []
        for rank, doc in enumerate(documents, 1):
            contexts.append({
                "rank": rank,
                "score": float(doc.score),
                "content": doc.content,
                "metadata": {
                    "file_path": doc.meta.get("file_path", "unknown"),
                    "source_id": doc.meta.get("source_id"),
                    "split_id": doc.meta.get("split_id"),
                    "split_idx_start": doc.meta.get("split_idx_start")
                }
            })
        
        # Extract answer
        answer = None
        if not retrieve_only:
            replies = result.get("llm", {}).get("replies", [])
            if replies:
                first_reply = replies[0]
                content = getattr(first_reply, "content", first_reply)
                if isinstance(content, list):
                    text_parts = []
                    for item in content:
                        item_text = getattr(item, "text", None)
                        if item_text is None:
                            if isinstance(item, dict) and "text" in item:
                                item_text = item["text"]
                            elif isinstance(item, str):
                                item_text = item
                        if item_text:
                            text_parts.append(item_text)
                    answer = "".join(text_parts) if text_parts else str(content)
                elif isinstance(content, str):
                    answer = content
                else:
                    answer = str(content)
        
        print(f"   📚 Retrieved {len(contexts)} chunks")
        if answer:
            print(f"   💬 Generated answer ({len(answer)} chars)")
        print(f"   ⏱️  {query_time:.2f}s\n")
        
        # Save trace
        query_trace = {
            "query_id": q["question_id"],
            "timestamp": datetime.now().isoformat(),
            "question": question_text,
            "category": q.get("category"),
            "difficulty": q.get("difficulty"),
            "retrieved_contexts": contexts,
            "generated_answer": answer,
            "num_contexts_retrieved": len(contexts),
            "query_time_seconds": round(query_time, 2)
        }
        traces["queries"].append(query_trace)
        
        time.sleep(0.5)  # Brief pause
    
    # Finalize
    session_end = datetime.now()
    traces["session_metadata"]["ended_at"] = session_end.isoformat()
    traces["session_metadata"]["total_queries"] = len(traces["queries"])
    traces["session_metadata"]["session_duration_seconds"] = round(
        (session_end - session_start).total_seconds(), 2
    )
    
    # Save
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"example_session_{session_id}.json"
    
    with open(output_file, 'w') as f:
        json.dump(traces, f, indent=2)
    
    print("=" * 70)
    print(f"✅ Example traces saved to: {output_file}")
    print(f"   {len(traces['queries'])} queries captured")
    print(f"   Session duration: {traces['session_metadata']['session_duration_seconds']}s")
    print("=" * 70)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate example traces with predefined questions")
    parser.add_argument("--retrieve-only", action="store_true",
                       help="Retrieve-only mode (no LLM generation)")
    parser.add_argument("--collection", type=str,
                       help="Qdrant collection name")
    parser.add_argument("--model", type=str,
                       help="LLM model to use (full RAG mode only)")
    parser.add_argument("--top-k", type=int, default=5,
                       help="Number of chunks to retrieve (default: 5)")
    parser.add_argument("--output-dir", type=str, default="traces",
                       help="Directory to save traces (default: traces/)")
    
    args = parser.parse_args()
    
    load_dotenv(PROJECT_ROOT / ".env")
    collection_name = args.collection or os.getenv("QDRANT_COLLECTION_PHASE1", "compliance_rag_v1")
    output_dir = PROJECT_ROOT / args.output_dir
    
    if args.retrieve_only:
        pipeline = create_retrieval_pipeline(collection_name=collection_name, top_k=args.top_k)
        generate_traces(
            pipeline, EXAMPLE_QUESTIONS, output_dir, retrieve_only=True,
            collection_name=collection_name, top_k=args.top_k
        )
    else:
        pipeline, llm_model = create_rag_pipeline(
            collection_name=collection_name,
            llm_model=args.model,
            top_k=args.top_k
        )
        generate_traces(
            pipeline, EXAMPLE_QUESTIONS, output_dir, retrieve_only=False,
            collection_name=collection_name, llm_model=llm_model, top_k=args.top_k
        )


if __name__ == "__main__":
    main()
