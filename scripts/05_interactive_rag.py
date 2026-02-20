# ============================================================================
# The Engineer's RAG Accelerator - Course Code
# Copyright (c) 2026 NeoSage. All rights reserved.
#
# This code is provided exclusively for enrolled students of the RAG Accelerator
# course. It may not be shared, redistributed, or used to create derivative works.
# See the Course Access Policy for full terms.
# ============================================================================

"""
Interactive RAG System - Query Your Compliance Knowledge Base
==============================================================

An interactive interface to explore your RAG system.
Ask questions about compliance requirements (CJIS, HIPAA, SOC2, NIST) and see the full pipeline in action!

Usage:
    # Full RAG mode (retrieve + generate)
    python 05_interactive_rag.py
    python 05_interactive_rag.py --model gemini-2.5-flash-lite

    # Retrieve-only mode (inspect chunks without LLM)
    python 05_interactive_rag.py --retrieve-only
"""

import os
import time
from pathlib import Path
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

# Get project root (script -> rag_pipeline -> week1_foundations -> root)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Available models (in order of preference for fallback)
AVAILABLE_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemma-3-27b"
]


def create_retrieval_pipeline(collection_name: str = None, top_k: int = 5):
    """
    Create a retrieval-only pipeline: Embedder -> Retriever

    Used for inspecting chunks without LLM generation.
    This is useful for understanding what the retriever returns
    before the LLM processes it.
    """
    load_dotenv(PROJECT_ROOT / ".env")

    # Configuration from environment
    collection_name = collection_name or os.getenv("QDRANT_COLLECTION_PHASE1", "compliance_rag_v1")
    fastembed_model = os.getenv("FASTEMBED_MODEL", "BAAI/bge-large-en-v1.5")

    print("Setting up retrieval pipeline (no LLM)...")
    print(f"  Embedding model: {fastembed_model}")
    print(f"  Collection: {collection_name}")
    print(f"  Top-K: {top_k}")

    # Connect to Qdrant document store
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

    # Build the pipeline - only embedder and retriever
    pipeline = Pipeline()

    # 1. Text Embedder - same model as indexing (critical!)
    text_embedder = FastembedTextEmbedder(model=fastembed_model, parallel=0, progress_bar=False)
    text_embedder.warm_up()
    pipeline.add_component("text_embedder", text_embedder)

    # 2. Retriever
    pipeline.add_component("retriever", QdrantEmbeddingRetriever(
        document_store=document_store,
        top_k=top_k
    ))

    # Connect embedder to retriever
    pipeline.connect("text_embedder.embedding", "retriever.query_embedding")

    print("Pipeline ready!\n")
    return pipeline


def create_rag_pipeline(collection_name: str = None, llm_model: str = None):
    """
    Create the complete RAG pipeline: Embedder -> Retriever -> Prompt Builder -> LLM

    Uses the same components as 04_test_rag_system.py:
    - FastEmbed with BAAI/bge-large-en-v1.5 for embeddings
    - Qdrant for vector retrieval
    - ChatPromptBuilder for prompt construction
    - GoogleGenAIChatGenerator (Gemini) for response generation
    """
    load_dotenv(PROJECT_ROOT / ".env")

    # Configuration from environment
    collection_name = collection_name or os.getenv("QDRANT_COLLECTION_PHASE1", "compliance_rag_v1")
    fastembed_model = os.getenv("FASTEMBED_MODEL", "BAAI/bge-large-en-v1.5")
    llm_model = llm_model or os.getenv("LLM_MODEL", "gemini-2.5-flash")

    print("Setting up RAG pipeline...")
    print(f"  Embedding model: {fastembed_model}")
    print(f"  LLM: {llm_model}")
    print(f"  Collection: {collection_name}")

    # Connect to Qdrant document store
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

    # Build the pipeline
    pipeline = Pipeline()

    # 1. Text Embedder - same model as indexing (critical!)
    text_embedder = FastembedTextEmbedder(model=fastembed_model, parallel=0, progress_bar=False)
    text_embedder.warm_up()
    pipeline.add_component("text_embedder", text_embedder)

    # 2. Retriever - top_k=5 chunks
    pipeline.add_component("retriever", QdrantEmbeddingRetriever(
        document_store=document_store,
        top_k=5
    ))

    # 3. Prompt Builder - system message + context + question
    template = [
        ChatMessage.from_system(
            "You are an expert compliance assistant specializing in CJIS, HIPAA, SOC 2, and NIST SP 800-53 requirements. "
            "Use the provided context to answer questions about compliance requirements with precise citations. "
            "Provide accurate, authoritative answers based on the regulatory documents."
        ),
        ChatMessage.from_user("""Context:
{% for document in documents %}
{{ document.content }}
---
{% endfor %}

Question: {{ question }}""")
    ]
    pipeline.add_component("prompt_builder", ChatPromptBuilder(
        template=template,
        required_variables=["documents", "question"]
    ))

    # 4. LLM - Gemini for generation
    pipeline.add_component("llm", GoogleGenAIChatGenerator(model=llm_model))

    # Connect the components
    pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
    pipeline.connect("retriever.documents", "prompt_builder.documents")
    pipeline.connect("prompt_builder.prompt", "llm.messages")

    print("Pipeline ready!\n")
    return pipeline, llm_model


def is_retryable_error(error_msg: str) -> bool:
    """Check if error is retryable (5xx server errors)."""
    retryable_patterns = ["503", "502", "500", "overloaded", "unavailable", "internal"]
    error_lower = error_msg.lower()
    return any(pattern in error_lower for pattern in retryable_patterns)


def generate_with_llm(llm, prompt_messages: list, model_name: str) -> tuple:
    """
    Run LLM generation. Returns (success, result_text, error_msg).
    """
    print(f"[4/4] Generating response ({model_name})...")
    generate_start = time.time()

    try:
        llm_result = llm.run(messages=prompt_messages)
        generate_time = time.time() - generate_start

        replies = llm_result.get("replies", [])
        if replies and replies[0].text:
            print(f"      Done ({generate_time:.2f}s)")
            return (True, replies[0].text, None)
        else:
            print("      No response generated")
            return (False, None, "Empty response")

    except Exception as e:
        error_msg = str(e)
        print(f"      Failed: {error_msg[:100]}")
        return (False, None, error_msg)


def ask_question(pipeline: Pipeline, question: str, current_model: str) -> tuple:
    """
    Run a question through the RAG pipeline and display the answer.

    Returns (success: bool, new_model: str or None).
    - success: True if answer was generated
    - new_model: If model was switched, returns new model name; else None
    """
    print("\n[1/4] Embedding query...")
    start_time = time.time()

    # Step 1: Embed the question
    embed_result = pipeline.get_component("text_embedder").run(text=question)
    embed_time = time.time() - start_time
    print(f"      Done ({embed_time:.2f}s)")

    # Step 2: Retrieve documents
    print("[2/4] Retrieving relevant documents...")
    retrieve_start = time.time()
    retrieve_result = pipeline.get_component("retriever").run(
        query_embedding=embed_result["embedding"]
    )
    retrieve_time = time.time() - retrieve_start
    documents = retrieve_result.get("documents", [])
    print(f"      Found {len(documents)} chunks ({retrieve_time:.2f}s)")

    # Show retrieved documents
    if documents:
        print("\n      Retrieved chunks:")
        for i, doc in enumerate(documents, 1):
            source = doc.meta.get('file_path', 'Unknown')
            source_name = Path(source).name if source != 'Unknown' else 'Unknown'
            content_preview = doc.content[:80].replace('\n', ' ') + "..."
            print(f"      [{i}] {source_name}")
            print(f"          \"{content_preview}\"")

    # Step 3: Build prompt
    print("\n[3/4] Building prompt...")
    prompt_result = pipeline.get_component("prompt_builder").run(
        documents=documents,
        question=question
    )
    print("      Done")

    # Step 4: Generate response (with retry logic)
    prompt_messages = prompt_result["prompt"]
    active_model = current_model
    switched_model = None

    while True:
        # Get the LLM to use
        if switched_model:
            # Create new LLM for switched model
            llm = GoogleGenAIChatGenerator(model=switched_model)
            active_model = switched_model
        else:
            llm = pipeline.get_component("llm")

        success, answer_text, error_msg = generate_with_llm(llm, prompt_messages, active_model)

        if success and answer_text:
            total_time = time.time() - start_time

            # Display the answer
            print("\n" + "=" * 60)
            print("ANSWER:")
            print("=" * 60)
            print(answer_text)

            # Show sources summary
            if documents:
                print("\nSources:")
                seen_sources = set()
                for doc in documents[:3]:
                    source = doc.meta.get('file_path', 'Unknown')
                    source_name = Path(source).name if source != 'Unknown' else 'Unknown'
                    if source_name not in seen_sources:
                        seen_sources.add(source_name)
                        print(f"  - {source_name}")

            print(f"\n[Total time: {total_time:.2f}s]")
            return (True, switched_model)

        # Generation failed - check if retryable
        if error_msg and is_retryable_error(error_msg):
            print(f"\n      Server error (retryable).")
            print("      Options:")
            print("        (r) Retry with same model")
            print("        (s) Switch to different model")
            print("        (n) Skip / new question")

            choice = input("      Choice [r/s/n]: ").strip().lower()

            if choice == 'r':
                print()
                continue  # Retry same model

            elif choice == 's':
                new_model = select_model(active_model)
                if new_model != active_model:
                    switched_model = new_model
                    print()
                    continue  # Retry with new model
                else:
                    print("      Model unchanged, retrying...")
                    print()
                    continue

            else:  # 'n' or anything else
                print("      Skipping.")
                return (False, switched_model)

        else:
            # Non-retryable error (4xx, auth, etc.)
            print(f"\n      Non-retryable error. Please check your configuration.")
            return (False, switched_model)


def print_chunk_details(doc, index: int) -> None:
    """Print full details of a retrieved chunk."""
    meta = doc.meta

    print(f"\n{'='*70}")
    print(f"CHUNK {index}")
    print(f"{'='*70}")

    # Score (similarity)
    if doc.score is not None:
        print(f"Score: {doc.score:.4f}")

    # Source information
    print(f"\nSource: {meta.get('file_path', 'Unknown')}")
    print(f"Split ID: {meta.get('split_id', 'N/A')}")
    print(f"Character Offset: {meta.get('split_idx_start', 'N/A')}")

    # Additional metadata if present
    if 'page_number' in meta:
        print(f"Page: {meta['page_number']}")
    if 'source_id' in meta:
        print(f"Source ID: {meta['source_id'][:20]}...")

    # Full content
    print(f"\nContent ({len(doc.content)} chars):")
    print("-" * 70)
    print(doc.content)
    print("-" * 70)


def retrieve_and_inspect(pipeline: Pipeline, question: str) -> None:
    """
    Run retrieval and display full chunk details.

    This uses pipeline.run() - the standard Haystack pattern -
    to execute the embedder and retriever components.
    """
    print(f"\nQuery: \"{question}\"")
    print("=" * 70)

    start_time = time.time()

    # Run the retrieval pipeline (embedder -> retriever)
    # This is the standard Haystack way to execute a pipeline
    result = pipeline.run({"text_embedder": {"text": question}})

    elapsed = time.time() - start_time

    # Get retrieved documents
    documents = result.get("retriever", {}).get("documents", [])

    print(f"\nRetrieved {len(documents)} chunks in {elapsed:.2f}s")

    if not documents:
        print("No chunks found for this query.")
        return

    # Display each chunk with full details
    for i, doc in enumerate(documents, 1):
        print_chunk_details(doc, i)

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Query: {question}")
    print(f"Chunks retrieved: {len(documents)}")
    print(f"Time: {elapsed:.2f}s")
    print("\nSources:")
    seen = set()
    for doc in documents:
        source = Path(doc.meta.get('file_path', 'Unknown')).name
        if source not in seen:
            seen.add(source)
            print(f"  - {source}")


def retrieve_only_loop(pipeline: Pipeline) -> None:
    """Interactive loop for retrieve-only mode (no LLM generation)."""
    print("=" * 60)
    print("  Compliance RAG System - Retrieve Only Mode")
    print("=" * 60)
    print("\nThis mode shows retrieved chunks WITHOUT LLM generation.")
    print("Use this to inspect what the retriever returns for your queries.")
    print("\nCommands:")
    print("  'quit' or 'exit' - Stop the program")
    print("\nExample queries:")
    print("  - What are the CJIS access control requirements?")
    print("  - What are HIPAA authentication requirements?")
    print("  - What are SOC 2 audit logging requirements?")
    print()

    while True:
        try:
            question = input("Query: ").strip()

            if not question:
                continue

            if question.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break

            retrieve_and_inspect(pipeline, question)
            print()

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")
            print("Please try again.\n")


def print_welcome(current_model: str):
    """Display welcome message and example queries."""
    print("=" * 60)
    print("  Compliance RAG System - Interactive Mode")
    print("=" * 60)
    print(f"\nCurrent LLM: {current_model}")
    print("\nAsk questions about compliance requirements (CJIS, HIPAA, SOC 2, NIST SP 800-53).")
    print("Commands:")
    print("  'quit' or 'exit' - Stop the program")
    print("  'model'          - Switch to a different LLM")
    print("\nExample questions to try:")
    print("  - What are the CJIS access control requirements?")
    print("  - What are the HIPAA encryption requirements?")
    print("  - What are the SOC 2 audit logging requirements?")
    print("  - What NIST controls apply to authentication?")
    print()


def select_model(current_model: str) -> str:
    """Let user select a different model."""
    print("\nAvailable models:")
    for i, model in enumerate(AVAILABLE_MODELS, 1):
        marker = " (current)" if model == current_model else ""
        print(f"  {i}. {model}{marker}")

    while True:
        try:
            choice = input("\nSelect model (1-3) or press Enter to cancel: ").strip()
            if not choice:
                return current_model
            idx = int(choice) - 1
            if 0 <= idx < len(AVAILABLE_MODELS):
                return AVAILABLE_MODELS[idx]
            print("Invalid choice. Please enter 1, 2, or 3.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def rebuild_pipeline_with_model(collection_name: str, new_model: str):
    """Rebuild the pipeline with a different LLM model."""
    print(f"\nSwitching to {new_model}...")
    return create_rag_pipeline(collection_name=collection_name, llm_model=new_model)


def interactive_loop(pipeline: Pipeline, current_model: str, collection_name: str) -> None:
    """Run the interactive question-answer loop."""
    print_welcome(current_model)

    while True:
        try:
            # Get user input
            question = input("Your question: ").strip()

            # Handle empty input
            if not question:
                continue

            # Handle exit commands
            if question.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break

            # Handle model switching
            if question.lower() == 'model':
                new_model = select_model(current_model)
                if new_model != current_model:
                    pipeline, current_model = rebuild_pipeline_with_model(collection_name, new_model)
                    print(f"Now using: {current_model}\n")
                else:
                    print("Model unchanged.\n")
                continue

            # Process the question
            success, switched_model = ask_question(pipeline, question, current_model)

            # If model was switched during retry, rebuild pipeline for next question
            if switched_model and switched_model != current_model:
                print(f"\nRebuilding pipeline with {switched_model} for future questions...")
                pipeline, current_model = rebuild_pipeline_with_model(collection_name, switched_model)

            print()  # Spacing between Q&A pairs

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")
            print("Please try again.\n")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Interactive RAG System for Compliance Documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Available models: {', '.join(AVAILABLE_MODELS)}

Examples:
    # Full RAG (retrieve + generate)
    python 05_interactive_rag.py
    python 05_interactive_rag.py --model gemini-2.5-flash-lite

    # Retrieve-only (inspect chunks, no LLM)
    python 05_interactive_rag.py --retrieve-only
    python 05_interactive_rag.py --retrieve-only --top-k 10
        """
    )
    parser.add_argument("--collection", help="Qdrant collection name (default: from .env)")
    parser.add_argument("--model", choices=AVAILABLE_MODELS, help="LLM model to use")
    parser.add_argument("--retrieve-only", action="store_true",
                        help="Retrieve-only mode: inspect chunks without LLM generation")
    parser.add_argument("--top-k", type=int, default=5,
                        help="Number of chunks to retrieve (default: 5)")
    args = parser.parse_args()

    try:
        load_dotenv(PROJECT_ROOT / ".env")
        collection_name = args.collection or os.getenv("QDRANT_COLLECTION_PHASE1", "compliance_rag_v1")

        if args.retrieve_only:
            # Retrieve-only mode: no LLM needed
            pipeline = create_retrieval_pipeline(
                collection_name=collection_name,
                top_k=args.top_k
            )
            retrieve_only_loop(pipeline)
        else:
            # Full RAG mode
            pipeline, current_model = create_rag_pipeline(
                collection_name=args.collection,
                llm_model=args.model
            )
            interactive_loop(pipeline, current_model, collection_name)

    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
