#!/usr/bin/env python3
"""
Capture RAG Session Traces for Evaluation
==========================================

Captures traces of RAG sessions for evaluation and debugging.
For each query, records:
- Question asked
- Retrieved chunks (with scores and metadata)
- Generated answer
- Query time and metadata

Traces are saved in JSON format: traces/session_YYYYMMDD_HHMMSS.json

Based on RAG Accelerator Week 2 trace capture methodology.

Usage:
    # Interactive mode with trace capture
    python scripts/06_capture_traces.py
    
    # Retrieve-only mode (no LLM generation)
    python scripts/06_capture_traces.py --retrieve-only
    
    # Specify custom output directory
    python scripts/06_capture_traces.py --output-dir custom_traces/
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
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

# Available models
AVAILABLE_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemma-3-27b"
]


def create_retrieval_pipeline(collection_name: str = None, top_k: int = 5):
    """Create a retrieval-only pipeline: Embedder -> Retriever"""
    load_dotenv(PROJECT_ROOT / ".env")
    
    collection_name = collection_name or os.getenv("QDRANT_COLLECTION_PHASE1", "compliance_rag_v1")
    fastembed_model = os.getenv("FASTEMBED_MODEL", "BAAI/bge-large-en-v1.5")
    
    print("Setting up retrieval pipeline (no LLM)...")
    print(f"  Embedding model: {fastembed_model}")
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
    doc_count = document_store.count_documents()
    print(f"  Connected to Qdrant ({doc_count} documents indexed)")
    
    pipeline = Pipeline()
    
    text_embedder = FastembedTextEmbedder(model=fastembed_model, parallel=0, progress_bar=False)
    text_embedder.warm_up()
    pipeline.add_component("text_embedder", text_embedder)
    
    pipeline.add_component("retriever", QdrantEmbeddingRetriever(
        document_store=document_store,
        top_k=top_k
    ))
    
    pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
    
    print("✅ Retrieval pipeline ready\n")
    return pipeline


def create_rag_pipeline(collection_name: str = None, llm_model: str = None, top_k: int = 5):
    """Create full RAG pipeline: Embedder -> Retriever -> Prompt Builder -> LLM"""
    load_dotenv(PROJECT_ROOT / ".env")
    
    collection_name = collection_name or os.getenv("QDRANT_COLLECTION_PHASE1", "compliance_rag_v1")
    fastembed_model = os.getenv("FASTEMBED_MODEL", "BAAI/bge-large-en-v1.5")
    llm_model = llm_model or os.getenv("LLM_MODEL", "gemini-2.5-flash")
    
    print("Setting up full RAG pipeline...")
    print(f"  Embedding model: {fastembed_model}")
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
    doc_count = document_store.count_documents()
    print(f"  Connected to Qdrant ({doc_count} documents indexed)")
    
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
    
    print("✅ RAG pipeline ready\n")
    return pipeline, llm_model


def query_pipeline(pipeline: Pipeline, question: str, retrieve_only: bool = False) -> Dict[str, Any]:
    """
    Query the pipeline and return structured results.
    
    Returns:
        Dict with retrieved_documents and answer (if full RAG)
    """
    # Run pipeline - include_outputs_from is critical to get retriever results!
    if retrieve_only:
        result = pipeline.run(
            {"text_embedder": {"text": question}},
            include_outputs_from={"text_embedder", "retriever"}
        )
    else:
        result = pipeline.run(
            {
                "text_embedder": {"text": question},
                "prompt_builder": {"question": question}
            },
            include_outputs_from={"text_embedder", "retriever", "prompt_builder", "llm"}
        )
    
    # Extract retrieved documents
    documents = result.get("retriever", {}).get("documents", [])
    
    # Extract answer if full RAG
    answer = None
    if not retrieve_only:
        replies = result.get("llm", {}).get("replies", [])
        if replies:
            answer = replies[0].content if hasattr(replies[0], 'content') else str(replies[0])
    
    return {
        "retrieved_documents": documents,
        "answer": answer
    }


def interactive_session_with_traces(
    pipeline: Pipeline,
    output_dir: Path,
    retrieve_only: bool = False,
    collection_name: str = "compliance_rag_v1",
    llm_model: str = None,
    top_k: int = 5
):
    """Interactive session that captures traces to JSON file."""
    
    print("=" * 70)
    print(f"  Compliance RAG - {'Retrieve-Only' if retrieve_only else 'Full RAG'} Mode")
    print("  WITH TRACE CAPTURE")
    print("=" * 70)
    print("\nExample questions:")
    print("  - What are the password requirements in CJIS?")
    print("  - How should audit logs be protected according to NIST?")
    print("  - What encryption is required for data at rest?")
    print("\nCommands:")
    print("  'quit' or 'exit' - Save traces and exit")
    print("=" * 70)
    print()
    
    # Session metadata
    session_start = datetime.now()
    session_id = session_start.strftime("%Y%m%d_%H%M%S")
    
    traces = {
        "session_metadata": {
            "session_id": session_id,
            "started_at": session_start.isoformat(),
            "mode": "retrieve_only" if retrieve_only else "full_rag",
            "collection": collection_name,
            "embedding_model": os.getenv("FASTEMBED_MODEL", "BAAI/bge-large-en-v1.5"),
            "llm_model": llm_model if not retrieve_only else None,
            "top_k": top_k
        },
        "queries": []
    }
    
    query_count = 0
    
    while True:
        try:
            question = input("\n🔍 Your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                break
                
            if not question:
                continue
            
            query_count += 1
            print(f"\n⏳ Processing query {query_count}...")
            start_time = time.time()
            
            # Query pipeline
            result = query_pipeline(pipeline, question, retrieve_only)
            query_time = time.time() - start_time
            
            # Extract retrieved contexts with metadata
            contexts = []
            for rank, doc in enumerate(result["retrieved_documents"], 1):
                context_meta = {
                    "rank": rank,
                    "score": float(doc.score),
                    "content": doc.content,
                    "metadata": {
                        "file_path": doc.meta.get("file_path", "unknown"),
                        "source_id": doc.meta.get("source_id"),
                        "split_id": doc.meta.get("split_id"),
                        "split_idx_start": doc.meta.get("split_idx_start")
                    }
                }
                contexts.append(context_meta)
            
            # Display results
            print(f"\n📊 Retrieved {len(contexts)} chunks (in {query_time:.2f}s)")
            for ctx in contexts:
                print(f"  [{ctx['rank']}] Score: {ctx['score']:.3f} | {ctx['metadata']['file_path']}")
                print(f"      Preview: {ctx['content'][:150]}...")
            
            # Display answer if full RAG
            if result["answer"]:
                print(f"\n💬 Answer ({len(result['answer'])} chars):")
                print(result["answer"])
            
            # Save trace
            query_trace = {
                "query_id": query_count,
                "timestamp": datetime.now().isoformat(),
                "question": question,
                "retrieved_contexts": contexts,
                "generated_answer": result["answer"],
                "num_contexts_retrieved": len(contexts),
                "query_time_seconds": round(query_time, 2)
            }
            traces["queries"].append(query_trace)
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            continue
    
    # Save traces
    if traces["queries"]:
        session_end = datetime.now()
        traces["session_metadata"]["ended_at"] = session_end.isoformat()
        traces["session_metadata"]["total_queries"] = len(traces["queries"])
        traces["session_metadata"]["session_duration_seconds"] = (session_end - session_start).total_seconds()
        
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"session_{session_id}.json"
        
        with open(output_file, 'w') as f:
            json.dump(traces, f, indent=2)
        
        print(f"\n✅ Session trace saved to: {output_file}")
        print(f"   {len(traces['queries'])} queries captured")
    else:
        print("\n⚠️  No queries captured")
    
    print("\n👋 Goodbye!")


def main():
    parser = argparse.ArgumentParser(
        description="Interactive RAG with trace capture for evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full RAG mode with trace capture
  python scripts/06_capture_traces.py
  
  # Retrieve-only mode (inspect chunks without LLM)
  python scripts/06_capture_traces.py --retrieve-only
  
  # Custom model and output directory
  python scripts/06_capture_traces.py --model gemini-2.5-flash-lite --output-dir my_traces/
        """
    )
    parser.add_argument("--retrieve-only", action="store_true",
                       help="Retrieve-only mode (no LLM generation)")
    parser.add_argument("--collection", type=str,
                       help="Qdrant collection name")
    parser.add_argument("--model", type=str, choices=AVAILABLE_MODELS,
                       help="LLM model to use (full RAG mode only)")
    parser.add_argument("--top-k", type=int, default=5,
                       help="Number of chunks to retrieve (default: 5)")
    parser.add_argument("--output-dir", type=str, default="traces",
                       help="Directory to save traces (default: traces/)")
    
    args = parser.parse_args()
    
    # Setup
    load_dotenv(PROJECT_ROOT / ".env")
    collection_name = args.collection or os.getenv("QDRANT_COLLECTION_PHASE1", "compliance_rag_v1")
    output_dir = PROJECT_ROOT / args.output_dir
    
    print(f"📁 Traces will be saved to: {output_dir}\n")
    
    # Create pipeline
    if args.retrieve_only:
        pipeline = create_retrieval_pipeline(collection_name=collection_name, top_k=args.top_k)
        interactive_session_with_traces(
            pipeline, output_dir, retrieve_only=True,
            collection_name=collection_name, top_k=args.top_k
        )
    else:
        pipeline, llm_model = create_rag_pipeline(
            collection_name=collection_name,
            llm_model=args.model,
            top_k=args.top_k
        )
        interactive_session_with_traces(
            pipeline, output_dir, retrieve_only=False,
            collection_name=collection_name, llm_model=llm_model, top_k=args.top_k
        )


if __name__ == "__main__":
    main()
