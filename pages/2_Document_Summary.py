import streamlit as st
from core.utils import get_db_conn
from core.nodes import get_llm_response

# --- Helper Functions ---

@st.cache_data
def get_doc_list():
    """Get list of available documents from the database."""
    conn = get_db_conn()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, filename FROM documentation_staging ORDER BY filename")
        doc_list = cursor.fetchall()
        cursor.close()
        conn.close()
        return doc_list
    except Exception as e:
        st.error(f"Failed to fetch document list: {e}")
        return []

def generate_oracle_summary(doc_id, num_paragraphs):
    """Generate summary using Oracle 23ai's built-in function."""
    conn = get_db_conn()
    if not conn:
        return "Database connection failed."
    
    try:
        cursor = conn.cursor()
        params_json = f'{{"provider": "database", "glevel": "Paragraph", "numParagraphs": {num_paragraphs}}}'
        
        cursor.execute('''
            SELECT dbms_vector_chain.utl_to_summary(
                dbms_vector_chain.utl_to_text((SELECT DATA FROM documentation_tab WHERE id = :doc_id)),
                JSON(:params_json)
            ) AS document_summary FROM dual
        ''', {'doc_id': doc_id, 'params_json': params_json})
        
        row = cursor.fetchone()
        summary_text = row[0] if row else "No summary could be generated."
        
        if hasattr(summary_text, 'read'):
            summary_text = summary_text.read()
        
        cursor.close()
        conn.close()
        return summary_text
    except Exception as e:
        return f"Failed to generate Oracle summary: {e}"

def enhance_summary_with_llm(summary_text, model_choice):
    """Enhances a given summary using an external LLM."""
    system_prompt = "You are an expert editor. Refine the following summary to improve its clarity, flow, and readability, while preserving the core information."
    user_prompt = f"Please refine this summary:\n\n{summary_text}"
    
    return get_llm_response(
        model_choice,
        system_prompt,
        user_prompt,
        temperature=0.5
    )

# --- Streamlit Application ---
st.set_page_config(page_title="Document Summarization", page_icon="📄", layout="wide")
st.title("Document Summarization")
st.markdown("Generate and enhance summaries of processed documents.")

# Get model choice from session state, default to Qwen
model_choice = st.session_state.get("model_choice", "Qwen")
st.info(f"Using **{model_choice}** model for enhancement. You can change this on the main chat page.")


doc_list = get_doc_list()

if not doc_list:
    st.warning("No documents found. Please ingest documents first.")
    st.stop()

doc_dict = {doc[1]: doc[0] for doc in doc_list}
selected_doc_name = st.selectbox(
    "Select a Document",
    options=doc_dict.keys(),
    help="Choose a document to summarize."
)

num_paragraphs = st.slider(
    "Summary Length (paragraphs)", 
    min_value=1, 
    max_value=5, 
    value=2,
    help="Adjust the desired length of the initial summary."
)

if st.button("Generate Summary", type="primary"):
    if selected_doc_name:
        doc_id = doc_dict[selected_doc_name]
        
        with st.spinner("Generating initial summary with Oracle 23ai..."):
            oracle_summary = generate_oracle_summary(doc_id, num_paragraphs)
        
        st.subheader("Oracle 23ai Summary")
        st.markdown(oracle_summary)

        with st.spinner(f"Enhancing summary with {model_choice}..."):
            enhanced_summary = enhance_summary_with_llm(oracle_summary, model_choice)

        st.subheader("Enhanced Summary")
        st.markdown(enhanced_summary)
