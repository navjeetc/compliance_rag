# ============================================================================
# The Engineer's RAG Accelerator - Course Code
# Copyright (c) 2026 NeoSage. All rights reserved.
#
# This code is provided exclusively for enrolled students of the RAG Accelerator
# course. It may not be shared, redistributed, or used to create derivative works.
# See the Course Access Policy for full terms.
# ============================================================================

"""
COMPLETE RAG PIPELINE: Embedder → Retriever → Prompt Builder → LLM
===================================================================

FIXED: GoogleGenAI integration matching working simple test
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

# Qdrant import for direct document store creation
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore
from haystack.utils import Secret

# Get project root (script -> scripts -> root)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

def create_complete_rag_pipeline(collection_name: str = None):
    """
    Create complete RAG pipeline: Embedder → Retriever → Prompt Builder → LLM
    """
    load_dotenv(PROJECT_ROOT / ".env")
    
    # Configuration
    collection_name = collection_name or os.getenv("QDRANT_COLLECTION_PHASE1", "compliance_rag_v1")
    fastembed_model = os.getenv("FASTEMBED_MODEL", "BAAI/bge-large-en-v1.5")
    llm_model = os.getenv("LLM_MODEL", "gemini-2.5-flash")
    
    print("🔧 Creating COMPLETE RAG Pipeline: Embedder → Retriever → Prompt Builder → LLM")
    print(f"🧠 Embedding: {fastembed_model}")
    print(f"🤖 LLM: {llm_model}")
    print(f"📊 Collection: {collection_name}")
    
    # Create document store inline
    try:
        document_store = QdrantDocumentStore(
            url=os.getenv("QDRANT_URL"),
            index=collection_name,
            api_key=Secret.from_env_var("QDRANT_API_KEY"),
            embedding_dim=int(os.getenv("EMBEDDING_DIMENSION", "1024")),
            recreate_index=False,  # Connect to existing collection
            return_embedding=True,
            wait_result_from_api=True
        )
        doc_count = document_store.count_documents()
        print(f"✅ Qdrant connectivity confirmed - Collection has {doc_count} documents")
        
    except Exception as e:
        print(f"❌ Qdrant connectivity failed: {str(e)}")
        raise
    
    # Create pipeline
    pipeline = Pipeline()
    
    # 1. Text Embedder (FastEmbed)
    text_embedder = FastembedTextEmbedder(
        model=fastembed_model,
        parallel=0
    )
    print("   Warming up text embedder...")
    text_embedder.warm_up()
    
    pipeline.add_component("text_embedder", text_embedder)
    
    # 2. Retriever (Qdrant)
    pipeline.add_component("retriever", QdrantEmbeddingRetriever(
        document_store=document_store,
        top_k=5
    ))
    
    # 3. Chat Prompt Builder - SIMPLIFIED like working version
    template = [
        ChatMessage.from_system("You are an expert compliance assistant specializing in CJIS, HIPAA, SOC 2, and NIST SP 800-53 requirements. Use the provided context to answer questions about compliance requirements with precise citations. Provide accurate, authoritative answers based on the regulatory documents."),
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
    
    # 4. GoogleGenAI Chat Generator - EXACT same as working simple test
    pipeline.add_component("llm", GoogleGenAIChatGenerator(model=llm_model))
    
    # 🔧 ALL CONNECTIONS
    print("🔗 Connecting all components...")
    try:
        # Connection 1: text_embedder → retriever
        pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
        print("   ✅ text_embedder → retriever connected")
        
        # Connection 2: retriever → prompt_builder  
        pipeline.connect("retriever.documents", "prompt_builder.documents")
        print("   ✅ retriever → prompt_builder connected")
        
        # Connection 3: prompt_builder → llm
        pipeline.connect("prompt_builder.prompt", "llm.messages")
        print("   ✅ prompt_builder → llm connected")
        
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        raise
    
    print("✅ Complete RAG pipeline created successfully!")
    
    # Debug info
    print("🔍 DEBUG - Pipeline Graph:")
    print(f"   Components: {list(pipeline.graph.nodes.keys())}")
    print(f"   Connections: {list(pipeline.graph.edges.keys())}")
    
    return pipeline

def test_complete_rag_pipeline(pipeline: Pipeline, question: str):
    """Test the complete RAG pipeline with working GoogleGenAI approach"""
    
    print(f"\n🧪 Testing COMPLETE RAG pipeline: '{question}'")
    print("-" * 60)
    
    try:
        start_time = time.time()
        
        # Run complete pipeline with debug outputs
        result = pipeline.run(
            {
                "text_embedder": {"text": question},
                "prompt_builder": {"question": question}
            },
            include_outputs_from={"text_embedder", "retriever", "prompt_builder", "llm"}
        )
        
        response_time = time.time() - start_time
        
        # Debug: Print all result keys
        print(f"🔍 DEBUG - Result keys: {list(result.keys())}")
        
        # Check each component
        if "text_embedder" in result:
            embedding = result["text_embedder"].get("embedding")
            if embedding:
                print(f"✅ text_embedder: Generated embedding (length: {len(embedding)})")
            else:
                print(f"❌ text_embedder: No embedding generated")
        
        if "retriever" in result:
            documents = result["retriever"].get("documents", [])
            print(f"✅ retriever: Retrieved {len(documents)} documents")
        else:
            print("❌ retriever: Not in results")
        
        if "prompt_builder" in result:
            prompt = result["prompt_builder"].get("prompt")
            if prompt:
                print(f"✅ prompt_builder: Generated prompt")
                # DEBUG: Show the actual prompt content
                if isinstance(prompt, list) and len(prompt) > 0:
                    user_message = prompt[-1]
                    user_content = str(user_message)
                    print(f"🔍 User message length: {len(user_content)}")
                    
                    # Check if template was rendered
                    if "{{" in user_content or "{%" in user_content:
                        print(f"❌ TEMPLATE NOT RENDERED - still has {{ or {{% symbols")
                        print(f"🔍 Raw content: {user_content[:500]}...")
                    else:
                        print(f"✅ Template rendered successfully")
                        print(f"🔍 Context preview: {user_content[:200]}...")
            else:
                print(f"❌ prompt_builder: No prompt generated")
        else:
            print("❌ prompt_builder: Not in results")
        
        # FIXED: Use same approach as working simple test
        if "llm" in result:
            replies = result["llm"].get("replies", [])
            if replies and len(replies) > 0:
                print(f"✅ llm: Generated {len(replies)} replies")
                
                reply = replies[0]
                print(f"🔍 Reply type: {type(reply)}")
                
                # Use EXACT same approach as working simple test
                if reply.text and len(reply.text.strip()) > 0:
                    print(f"\n💬 **FINAL ANSWER:**")
                    print(f"{reply.text}")
                    
                    # Show sources
                    if "retriever" in result:
                        retrieved_docs = result["retriever"]["documents"]
                        if retrieved_docs:
                            print(f"\n📚 **Sources:**")
                            for i, doc in enumerate(retrieved_docs[:3], 1):
                                source = doc.meta.get('file_path', 'Unknown')
                                try:
                                    from pathlib import Path
                                    source_name = Path(source).name if source != 'Unknown' else 'Unknown'
                                except:
                                    source_name = str(source)
                                print(f"   {i}. {source_name}")
                    
                    print(f"\n⚡ Response time: {response_time:.2f}s")
                    return True
                else:
                    print(f"\n❌ **EMPTY RESPONSE from GoogleGenAI**")
                    print(f"🔍 Reply text: '{reply.text}'")
                    print(f"🔍 Reply._content: {getattr(reply, '_content', 'NOT_FOUND')}")
                    
                    # Test GoogleGenAI directly with same prompt
                    print(f"\n🧪 Testing GoogleGenAI directly with same prompt...")
                    try:
                        generator = GoogleGenAIChatGenerator(model="gemini-2.5-flash")
                        if "prompt_builder" in result:
                            prompt_messages = result["prompt_builder"]["prompt"]
                            direct_result = generator.run(messages=prompt_messages)
                            if direct_result["replies"] and direct_result["replies"][0].text:
                                print(f"✅ Direct test works: {direct_result['replies'][0].text[:100]}...")
                                print(f"❌ Issue is in pipeline, not GoogleGenAI")
                            else:
                                print(f"❌ Direct test also fails - issue is with prompt or API")
                    except Exception as e:
                        print(f"❌ Direct test error: {e}")
                    
                    return False
            else:
                print(f"❌ llm: No replies generated")
                return False
        else:
            print("❌ llm: Not in results")
            return False
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Complete RAG Pipeline")
    parser.add_argument("--collection", help="Collection name")
    parser.add_argument("--query", help="Single test query")
    args = parser.parse_args()
    
    print("🚀 COMPLETE RAG PIPELINE TEST")
    print("=" * 50)
    
    try:
        # Create complete pipeline
        pipeline = create_complete_rag_pipeline(collection_name=args.collection)
        
        # Test with a query
        test_query = args.query or "What are the CJIS access control requirements?"
        
        success = test_complete_rag_pipeline(pipeline, test_query)
        
        if success:
            print(f"\n🎉 🎉 🎉 COMPLETE RAG PIPELINE WORKING! 🎉 🎉 🎉")
            print("   Phase 1 baseline RAG pipeline is complete!")
        else:
            print(f"\n❌ Complete RAG pipeline test failed!")
            exit(1)
        
    except Exception as e:
        print(f"\n💥 Error: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    main()