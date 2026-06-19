import streamlit as st
import os
import json
import time
from src import config
from src.classifier import classify_customer_persona
from src.rag_pipeline import LocalRAGPipeline
from src.generator import generate_adaptive_response
from src.escalator import check_escalation_triggers

# Page Configuration & Aesthetics
st.set_page_config(
    page_title="Adsparkx Persona Support Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium CSS Injection (Glassmorphism & Gradients)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main Background & Title */
    .title-banner {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(30, 60, 114, 0.2);
        position: relative;
        overflow: hidden;
    }
    
    .title-banner::after {
        content: "";
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.15) 0%, transparent 60%);
        pointer-events: none;
    }
    
    .title-banner h1 {
        margin: 0;
        font-weight: 700;
        font-size: 2.2rem;
        letter-spacing: -0.5px;
    }
    
    .title-banner p {
        margin: 0.5rem 0 0 0;
        font-weight: 300;
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    /* Persona Badges */
    .badge {
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
        margin-right: 6px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .badge-tech {
        background-color: rgba(0, 229, 255, 0.15);
        color: #00b0ff;
        border: 1px solid rgba(0, 229, 255, 0.3);
    }
    
    .badge-frustrated {
        background-color: rgba(255, 23, 68, 0.15);
        color: #ff1744;
        border: 1px solid rgba(255, 23, 68, 0.3);
    }
    
    .badge-exec {
        background-color: rgba(255, 215, 0, 0.15);
        color: #ffd700;
        border: 1px solid rgba(255, 215, 0, 0.3);
    }
    
    .badge-positive {
        background-color: rgba(0, 230, 118, 0.15);
        color: #00e676;
        border: 1px solid rgba(0, 230, 118, 0.3);
    }
    
    .badge-neutral {
        background-color: rgba(158, 158, 158, 0.15);
        color: #9e9e9e;
        border: 1px solid rgba(158, 158, 158, 0.3);
    }
    
    /* Chat Bubble Layouts */
    .chat-bubble {
        padding: 1.2rem;
        border-radius: 16px;
        margin-bottom: 1rem;
        line-height: 1.5;
        box-shadow: 0 4px 15px rgba(0,0,0,0.02);
        max-width: 85%;
    }
    
    .chat-user {
        background-color: #f0f4f9;
        color: #1e293b;
        margin-left: auto;
        border-bottom-right-radius: 4px;
        border-left: 4px solid #2a5298;
    }
    
    .chat-assistant {
        background-color: #ffffff;
        color: #0f172a;
        margin-right: auto;
        border-bottom-left-radius: 4px;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #10b981;
    }
    
    .chat-escalated {
        background-color: #fff5f5;
        color: #991b1b;
        margin-right: auto;
        border-bottom-left-radius: 4px;
        border: 1px solid #fecaca;
        border-left: 4px solid #dc2626;
    }
    
    /* Sidebar Widgets Styling */
    .sidebar-section {
        background: rgba(255, 255, 255, 0.05);
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Micro-animations */
    .hover-card {
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .hover-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.06);
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "escalated" not in st.session_state:
    st.session_state.escalated = False
if "last_classification" not in st.session_state:
    st.session_state.last_classification = None
if "last_sources" not in st.session_state:
    st.session_state.last_sources = []
if "last_system_prompt" not in st.session_state:
    st.session_state.last_system_prompt = ""
if "last_handoff" not in st.session_state:
    st.session_state.last_handoff = None
if "api_key" not in st.session_state:
    st.session_state.api_key = config.GEMINI_API_KEY

# Update global config API key dynamically if overridden in UI
config.GEMINI_API_KEY = st.session_state.api_key

# Initialize RAG Pipeline Instance
if "rag" not in st.session_state:
    st.session_state.rag = LocalRAGPipeline()
    # Auto-ingest files on startup if DB count is 0
    try:
        if st.session_state.rag.collection.count() == 0:
            st.session_state.rag.ingest_directory("data")
    except Exception:
        pass

# Helper function to reset chat
def reset_chat_session():
    st.session_state.messages = []
    st.session_state.escalated = False
    st.session_state.last_classification = None
    st.session_state.last_sources = []
    st.session_state.last_system_prompt = ""
    st.session_state.last_handoff = None

# Title Banner
st.markdown("""
<div class="title-banner">
    <h1>🤖 Persona-Adaptive Customer Support Agent</h1>
    <p>Advanced LLM + RAG System with Cognitive Tone Classification and Human Escalation Protocol</p>
</div>
""", unsafe_allow_html=True)

# Layout Setup: Left Sidebar (Controls) & Right Main Workspace (Tabs)
with st.sidebar:
    st.markdown("### 🔑 API Authentication")
    api_key_input = st.text_input(
        "Google Gemini API Key",
        value=st.session_state.api_key,
        type="password",
        help="Input your Gemini API key. If empty, the app uses config fallback variables."
    )
    if api_key_input != st.session_state.api_key:
        st.session_state.api_key = api_key_input
        config.GEMINI_API_KEY = api_key_input
        # Re-initialize RAG client with new key
        st.session_state.rag = LocalRAGPipeline()
        st.success("API Key updated successfully!")
        
    st.divider()

    st.markdown("### ⚙️ System Configuration")
    conf_threshold = st.slider(
        "RAG Retrieval Confidence Threshold",
        min_value=0.0,
        max_value=1.0,
        value=config.RETRIEVAL_CONFIDENCE_THRESHOLD,
        step=0.05,
        help="Cosine similarity score limit. Below this triggers escalation."
    )
    
    max_frust = st.number_input(
        "Max Consecutive Frustrated Turns",
        min_value=1,
        max_value=5,
        value=config.MAX_CONSECUTIVE_FRUSTRATION,
        help="Trigger escalation after this many consecutive user turns showing frustration/anger."
    )
    
    st.divider()
    
    st.markdown("### 📊 Database & Index Control")
    try:
        total_docs = st.session_state.rag.collection.count()
    except Exception:
        total_docs = 0
    st.metric("Total Indexed Chunks", total_docs)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Rebuild Index", use_container_width=True):
            with st.spinner("Indexing support articles..."):
                st.session_state.rag.reset_database()
                # Ensure PDF is generated if deleted
                if not os.path.exists("data/password_reset_guide.pdf"):
                    try:
                        import generate_pdf
                        generate_pdf.generate_pdf()
                    except Exception:
                        pass
                chunks = st.session_state.rag.ingest_directory("data")
                st.success(f"Indexed {chunks} chunks!")
                time.sleep(1)
                st.rerun()
    with col2:
        if st.button("🗑️ Clear Index", use_container_width=True):
            st.session_state.rag.reset_database()
            st.warning("Index cleared.")
            time.sleep(1)
            st.rerun()

    st.divider()
    st.button("🧹 Clear Chat History", on_click=reset_chat_session, use_container_width=True)

# Main Application Area: Tab Navigation
tab_chat, tab_docs, tab_logs = st.tabs([
    "💬 Active Support Chat", 
    "📂 Document Library", 
    "⚙️ Live System Logs"
])

# ==================== TAB 1: SUPPORT CHAT ====================
with tab_chat:
    # Setup test scenario buttons at the top of the chat tab
    st.markdown("##### 🚀 Fast Testing Scenarios")
    cols = st.columns(5)
    
    scenarios = [
        {"name": "1. Frustrated User", "query": "Where is the guide to clear cookies? It's been an hour and nothing is loading on your interface!"},
        {"name": "2. Tech Expert", "query": "What are the header parameter requirements for your bearer token auth implementation?"},
        {"name": "3. Business Exec", "query": "Our operational uptime is decreasing. We need a timeline of when billing disputes are resolved."},
        {"name": "4. DB Issue (RAG)", "query": "I'm experiencing an issue with your database integration that's causing internal errors."},
        {"name": "5. Refund Demand", "query": "My billing statement has unexpected duplicate charges. I demand an immediate refund!"}
    ]
    
    selected_scenario_query = None
    for idx, sc in enumerate(scenarios):
        with cols[idx]:
            if st.button(sc["name"], key=f"scenario_btn_{idx}", use_container_width=True):
                selected_scenario_query = sc["query"]

    st.divider()

    # Conversation History Display
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            # Choose bubble class depending on status
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="chat-bubble chat-user">
                    <b>You</b> <br/>
                    {msg['text']}<br/>
                    <div style='margin-top: 6px;'>
                        <span class="badge {'badge-tech' if msg.get('persona') == 'Technical Expert' else 'badge-frustrated' if msg.get('persona') == 'Frustrated User' else 'badge-exec'}">{msg.get('persona', 'Unknown')}</span>
                        <span class="badge badge-neutral">{msg.get('sentiment', 'Neutral')}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                if msg.get("escalated"):
                    st.markdown(f"""
                    <div class="chat-bubble chat-escalated">
                        <b>🚨 Human Support Escalation</b> <br/>
                        {msg['text']}
                    </div>
                    """, unsafe_allow_html=True)
                    # Display the Handoff JSON Report inside an expander
                    with st.expander("📄 Click to View / Copy Handoff Ticket JSON", expanded=True):
                        st.json(msg.get("handoff", {}))
                else:
                    st.markdown(f"""
                    <div class="chat-bubble chat-assistant">
                        <b>Support Agent</b><br/>
                        {msg['text']}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Display Retrieved Sources in Expander
                    if msg.get("sources"):
                        with st.expander("🔍 Retrieved Sources & Confidence Scores"):
                            for s in msg["sources"]:
                                score = s["score"]
                                progress_val = min(1.0, max(0.0, score))
                                st.write(f"📂 **{s['source']}** (Page: {s['page']})")
                                st.progress(progress_val)
                                st.write(f"Confidence Score: `{score:.4f}`")
                                st.info(f"Chunk Snippet: *\"{s['text']}\"*")

    # Handle Escalation banner
    if st.session_state.escalated:
        st.warning("⚠️ **This conversation has been escalated to a live human representative.** The AI agent is currently offline. Reset the chat history to start a new session.")

    # User Input Field
    user_input = st.chat_input("Type your message here...", disabled=st.session_state.escalated)
    
    # Process user query (either from chat input or scenario buttons)
    query_to_process = None
    if selected_scenario_query:
        query_to_process = selected_scenario_query
    elif user_input:
        query_to_process = user_input
        
    if query_to_process:
        # Append User Message to history
        st.session_state.messages.append({
            "role": "user",
            "text": query_to_process,
            "persona": "Pending...",
            "sentiment": "Pending..."
        })
        
        with st.spinner("Analyzing message tone & retrieving context..."):
            # 1. Run Persona & Sentiment Classifier
            classification = classify_customer_persona(query_to_process)
            st.session_state.last_classification = classification
            
            # Update last message's classification in history
            st.session_state.messages[-1]["persona"] = classification["persona"]
            st.session_state.messages[-1]["sentiment"] = classification["sentiment"]
            
            # 2. Query RAG Database
            context_chunks = st.session_state.rag.retrieve_context(query_to_process, top_k=3)
            st.session_state.last_sources = context_chunks
            
            # 3. Check Escalation Engine
            # Pass full chat history to evaluate consecutive frustration counts
            escalation_check = check_escalation_triggers(
                user_query=query_to_process,
                persona_data=classification,
                context_chunks=context_chunks,
                chat_history=st.session_state.messages,
                override_threshold=conf_threshold,
                override_max_frustration=max_frust
            )
            
            # 4. Generate Response based on Escalation Check
            if escalation_check["escalated"]:
                st.session_state.escalated = True
                response_text = "I apologize, but this query requires human support. I have generated a handoff ticket and am connecting you with a live specialist."
                handoff_summary = escalation_check["handoff_summary"]
                st.session_state.last_handoff = handoff_summary
                
                # Append Escalation Message
                st.session_state.messages.append({
                    "role": "assistant",
                    "text": response_text,
                    "escalated": True,
                    "handoff": handoff_summary
                })
            else:
                # Normal Response Generation
                response_data = generate_adaptive_response(
                    user_query=query_to_process,
                    persona=classification["persona"],
                    context_chunks=context_chunks
                )
                
                st.session_state.last_system_prompt = response_data["system_prompt"]
                
                # Append Agent Message
                st.session_state.messages.append({
                    "role": "assistant",
                    "text": response_data["response"],
                    "escalated": False,
                    "sources": context_chunks
                })
                
        st.rerun()

# ==================== TAB 2: DOCUMENT LIBRARY ====================
with tab_docs:
    st.markdown("### 📂 Help Desk Knowledge Base Files")
    st.write("These files reside in the `data/` directory and are used by the RAG model to retrieve facts and compile replies.")
    
    data_dir = "data"
    if os.path.exists(data_dir):
        files = [f for f in os.listdir(data_dir) if os.path.isfile(os.path.join(data_dir, f))]
        
        if not files:
            st.info("No documents found in `data/`. Put support articles there or click **Rebuild Index** in the sidebar to create sample documents.")
        else:
            col_list, col_preview = st.columns([1, 2])
            with col_list:
                selected_file = st.radio("Select Document to Preview:", files)
                
            with col_preview:
                st.markdown(f"#### Previewing: `{selected_file}`")
                file_path = os.path.join(data_dir, selected_file)
                
                if selected_file.endswith('.pdf'):
                    st.info("💡 PDF documents contain binary formatting. Below is the text content extracted from the file pages:")
                    try:
                        reader = PdfReader(file_path)
                        for page_num, page in enumerate(reader.pages):
                            st.write(f"**--- Page {page_num + 1} ---**")
                            st.text(page.extract_text())
                    except Exception as e:
                        st.error(f"Error reading PDF content: {e}")
                else:
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            file_content = f.read()
                        if selected_file.endswith('.md'):
                            st.markdown(file_content)
                        else:
                            st.text_area("File Content:", file_content, height=400)
                    except Exception as e:
                        st.error(f"Error reading file content: {e}")
    else:
        st.error("`data/` directory does not exist. Please index files or build directory structure.")

# ==================== TAB 3: SYSTEM LOGS ====================
with tab_logs:
    st.markdown("### ⚙️ Real-time Diagnostic Dashboard")
    st.write("This log trace displays internal data structures from the last interaction to verify correctness of LLM configurations.")
    
    col_class, col_rag = st.columns(2)
    with col_class:
        st.markdown("#### 💬 Classification Results")
        if st.session_state.last_classification:
            st.write(st.session_state.last_classification)
            persona = st.session_state.last_classification.get("persona")
            sentiment = st.session_state.last_classification.get("sentiment")
            
            st.markdown(f"**Persona Badge:** <span class='badge {'badge-tech' if persona == 'Technical Expert' else 'badge-frustrated' if persona == 'Frustrated User' else 'badge-exec'}'>{persona}</span>", unsafe_allow_html=True)
            st.markdown(f"**Sentiment Badge:** <span class='badge badge-positive'>{sentiment}</span>", unsafe_allow_html=True)
        else:
            st.info("No classification log data generated yet. Submit a message in the chat tab.")

    with col_rag:
        st.markdown("#### 🔍 RAG Retrieval Output")
        if st.session_state.last_sources:
            for idx, source in enumerate(st.session_state.last_sources):
                st.markdown(f"**Source {idx+1}:** `{source['source']}` (Confidence: `{source['score']:.4f}`)")
                st.code(source['text'])
        else:
            st.info("No RAG retrieval logs generated yet. Submit a query in the chat tab.")
            
    st.divider()
    
    st.markdown("#### 📜 Compiled System Prompt System Instructions")
    if st.session_state.last_system_prompt:
        st.code(st.session_state.last_system_prompt, language="markdown")
    else:
        st.info("No prompt compiles logged yet.")

    st.divider()

    st.markdown("#### 📄 Raw Handoff JSON Payload")
    if st.session_state.last_handoff:
        st.code(json.dumps(st.session_state.last_handoff, indent=2), language="json")
    else:
        st.info("Escalation protocol has not been triggered. No handoff payload.")
