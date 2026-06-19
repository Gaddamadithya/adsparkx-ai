import os
import sys
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import config
from src.classifier import classify_customer_persona
from src.rag_pipeline import LocalRAGPipeline
from src.generator import generate_adaptive_response
from src.escalator import check_escalation_triggers

def run_tests():
    print("=" * 60)
    print(" PERSONA-ADAPTIVE CUSTOMER SUPPORT AGENT INTEGRATION TEST ")
    print("=" * 60)
    
    print("\n[1] Environment Diagnostics:")
    print(f"  - GEMINI_API_KEY Configured: {'YES' if config.GEMINI_API_KEY else 'NO'}")
    print(f"  - Gemini Model Target: {config.GEMINI_MODEL}")
    print(f"  - Embedding Model Target: {config.EMBEDDING_MODEL}")
    print(f"  - Vector DB Directory: {config.CHROMA_DB_DIR}")
    print(f"  - Confidence Threshold: {config.RETRIEVAL_CONFIDENCE_THRESHOLD}")
    
    print("\n[2] Initializing RAG Pipeline & Ingesting documents...")
    rag = LocalRAGPipeline()
    # Reset and ingest to ensure a clean state
    rag.reset_database()
    indexed_count = rag.ingest_directory("data")
    print(f"  - Successfully indexed {indexed_count} total chunks in FAISS.")
    
    # 5 test queries matching requirements
    test_scenarios = [
        {
            "id": 1,
            "query": "Where is the guide to clear cookies? It's been an hour and nothing is loading on your interface!",
            "label": "Frustrated User (Empathetic / No Jargon / Action Steps)"
        },
        {
            "id": 2,
            "query": "What are the header parameter requirements for your bearer token auth implementation?",
            "label": "Technical Expert (Detailed / Code / System configs)"
        },
        {
            "id": 3,
            "query": "Our operational uptime is decreasing. We need a timeline of when billing disputes are resolved.",
            "label": "Business Executive (Brief / Outcome-oriented / Direct)"
        },
        {
            "id": 4,
            "query": "I'm experiencing an issue with your database integration that's causing internal errors.",
            "label": "Technical Expert (RAG search / Troubleshooting)"
        },
        {
            "id": 5,
            "query": "My billing statement has unexpected duplicate charges. I demand an immediate refund!",
            "label": "Escalation Check (Frustrated / Sensitive billing topic -> Instant Handoff JSON)"
        }
    ]

    print("\n[3] Executing Test Scenarios:")
    for test in test_scenarios:
        print("-" * 50)
        print(f"Scenario #{test['id']}: {test['label']}")
        print(f"User Message: \"{test['query']}\"")
        
        # A. Classify Persona & Sentiment
        classification = classify_customer_persona(test['query'])
        print(f"  - Detected Persona: {classification['persona']} (Confidence: {classification['confidence']})")
        print(f"  - Detected Sentiment: {classification['sentiment']}")
        print(f"  - Reasoning: {classification['reasoning']}")
        
        # B. Retrieve RAG context
        context = rag.retrieve_context(test['query'], top_k=2)
        print("  - Retrieved Chunks:")
        for idx, chunk in enumerate(context):
            print(f"    * Chunk {idx+1} Source: {chunk['source']} (Page: {chunk['page']}) | Similarity Score: {chunk['score']}")
            print(f"      Content Snippet: {chunk['text'][:120]}...")
            
        # C. Check Escalation Trigger
        # For simplicity in test, mock chat history has only current turn
        chat_history = [{"role": "user", "text": test['query'], "sentiment": classification['sentiment'], "persona": classification['persona']}]
        escalation_result = check_escalation_triggers(
            user_query=test['query'],
            persona_data=classification,
            context_chunks=context,
            chat_history=chat_history
        )
        
        print(f"  - Escalation Status: {'ESCALATED' if escalation_result['escalated'] else 'NORMAL'}")
        if escalation_result['escalated']:
            print(f"    Reason: {escalation_result['reason']}")
            print("    Handoff Report:")
            print(json.dumps(escalation_result['handoff_summary'], indent=4))
        else:
            # D. Generate Response
            response_data = generate_adaptive_response(
                user_query=test['query'],
                persona=classification['persona'],
                context_chunks=context
            )
            print("  - Generated Response:")
            print(f"\"\"\"\n{response_data['response']}\n\"\"\"")
            
    print("\n" + "=" * 60)
    print(" INTEGRATION TESTING COMPLETED ")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
