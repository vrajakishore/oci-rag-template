import streamlit as st
from datetime import datetime
from core.graphs import create_rag_graph
from core.utils import get_db_conn


# --- Streamlit Application ---
st.set_page_config(page_title="RAG Agent", page_icon="🤖", layout="wide")

# Header with logo
# Add logo if available
#st.image("gra-logo.svg", width=100)
st.title("RAG Template - Agent v3")

# --- Helper Functions ---
def get_system_stats():
    """Get system statistics for dashboard"""
    conn = get_db_conn()
    if not conn:
        return None, None, None
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM documentation_staging")
        total_docs = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT doc_id) FROM doc_chunks WHERE doc_id IS NOT NULL")
        processed_docs = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM doc_chunks")
        total_chunks = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return total_docs, processed_docs, total_chunks
    except Exception as e:
        st.warning(f"Could not load statistics: {e}")
        return None, None, None

# --- UI Components ---
# Dashboard with statistics
col1, col2, col3 = st.columns(3)
total_docs, processed_docs, total_chunks = get_system_stats()

if total_docs is not None:
    with col1:
        st.metric("📄 Total Documents", total_docs)
    with col2:
        st.metric("✅ Processed Documents", processed_docs)
    with col3:
        st.metric("🧩 Available Chunks", total_chunks)

st.markdown("---")

# Help section
with st.expander("How to Use This Agent", expanded=False):
    st.markdown("""
    ### How it Works:
    - This agent uses a graph-based RAG pipeline to answer your questions.
    - It can rewrite your question for better search, retrieve relevant documents, and generate answers.
    - The graph structure allows for more complex and robust query handling.
    """)

# Initialize chat history
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Sidebar configuration
with st.sidebar:
    st.header("Configuration")
    model_choice = st.selectbox(
        "Select Language Model:",
        ["Qwen", "OCI GenAI"],
        key="model_choice",
        help="Choose between OCI GenAI or the Qwen model"
    )
    st.markdown("---")
    st.markdown("### Chat Management")
    if st.button("Reset Chat", type="secondary", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    if st.session_state.messages:
        st.info(f"Current conversation: {len(st.session_state.messages)} messages")

# Display chat history
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # Add a download button for assistant messages
        if message["role"] == "assistant":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                label="📥 Save Response",
                data=message["content"],
                file_name=f"RAG_Agent_Response_{timestamp}_{i}.md",
                mime="text/markdown",
                key=f"download_{i}" # Unique key for each button
            )

# Chat input and processing
if prompt := st.chat_input("Ask your question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Generate assistant response
    with st.spinner("Processing your request..."):
        app = create_rag_graph()
        inputs = {
            "question": prompt, 
            "chat_history": st.session_state.get('messages', []),
            "model_choice": st.session_state.model_choice,
        }
        
        response_text = ""
        citations = []
        
        # Stream the graph output and capture the final answer
        for output in app.stream(inputs):
            for key, value in output.items():
                if key in ["generate_answer", "synthesize_comparison", "run_summarization", "run_training_generation"]:
                    response_text = value.get("answer", "")
                    citations = value.get("citations", [])
                elif key in ["handle_greeting", "handle_give_up"]:
                    response_text = value.get("answer", "")

        if citations:
            response_text += "\n\n**Sources:**\n" + "\n".join([f"• {c}" for c in citations])
        
        if not response_text:
            response_text = "I could not find an answer to your question."

    # Add response to session state and rerun to display everything
    st.session_state.messages.append({"role": "assistant", "content": response_text})
    st.rerun()


# Footer
st.markdown("---")
st.markdown("**Note:** This system uses Oracle 23ai, LangChain, and LangGraph.")
