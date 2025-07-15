import streamlit as st
import requests
import json
from langchain_core.prompts import PromptTemplate
from langchain_community.chat_models import ChatOCIGenAI
from langchain_core.messages import HumanMessage
from core.utils import get_db_conn
from config import (
    QWEN_ENDPOINT,
    QWEN3_CONTEXT_LIMIT_CHARS,
    OCI_GENAI_CONTEXT_LIMIT_CHARS,
    GENAI_ENDPOINT,
    GENAI_MODEL_ID,
    GENAI_COMPARTMENT_ID,
    OCI_AUTH_TYPE,
    OCI_CONFIG_PROFILE,
)

def get_llm_response(model_choice: str, system_prompt: str, user_prompt: str, json_mode: bool = False, **kwargs) -> str:
    """Helper function to call the appropriate LLM."""
    if model_choice == "OCI GenAI":
        try:
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            chat = ChatOCIGenAI(
                model_id=GENAI_MODEL_ID,
                service_endpoint=GENAI_ENDPOINT,
                compartment_id=GENAI_COMPARTMENT_ID,
                provider="cohere",
                auth_type=OCI_AUTH_TYPE,
                auth_profile=OCI_CONFIG_PROFILE,
                model_kwargs=kwargs
            )
            if json_mode:
                # Cohere model on OCI GenAI supports JSON mode via additional params
                chat.model_kwargs['response_format'] = {"type": "json_object"}

            response = chat.invoke([HumanMessage(content=full_prompt)])
            return response.content.strip()
        except Exception as e:
            st.error(f"Error communicating with OCI GenAI: {e}")
            return f"Error: Could not connect to the OCI GenAI language model."

    else: # Default to Qwen
        payload = {
            "model": "Qwen/Qwen3-4B",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2,
            "chat_template_kwargs": {"enable_thinking": False},
            **kwargs,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        try:
            response = requests.post(QWEN_ENDPOINT, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
        except requests.exceptions.RequestException as e:
            st.error(f"Network error calling Qwen model: {e}")
            return f"Error: Could not connect to the language model."
        except Exception as e:
            st.error(f"Error processing Qwen response: {e}")
            return "Error: Invalid response from the language model."


def classify_intent(state):
    """
    Classifies the user's intent to route to the appropriate workflow.
    """
    question = state["question"].lower().strip()
    model_choice = state["model_choice"]

    # Rule-based checks
    greetings = ["hello", "hi", "hey", "bye", "good morning", "good afternoon", "good evening"]
    if question in greetings:
        return "greeting"

    comparison_starters = ["compare", "what are the differences", "contrast"]
    if any(question.startswith(starter) for starter in comparison_starters):
        return "comparison"

    summarization_starters = ["summarize", "give me a summary", "tell me about"]
    if any(question.startswith(starter) for starter in summarization_starters):
        return "summarization"

    training_starters = ["create a quiz", "generate training", "make a lesson plan"]
    if any(question.startswith(starter) for starter in training_starters):
        return "training_generation"

    # Fallback to LLM for more nuanced classification
    system_prompt = (
        "You are an intent classification expert. Classify the user's input into one of the following categories: "
        "'greeting', 'comparison', 'summarization', 'training_generation', or 'rag_query'.\n"
        "- 'greeting': For simple social greetings.\n"
        "- 'comparison': For requests to compare, contrast, or find differences.\n"
        "- 'summarization': For requests to summarize a topic or document.\n"
        "- 'training_generation': For requests to create training materials like quizzes or lesson plans.\n"
        "- 'rag_query': For all other questions seeking information.\n"
        "Respond with only the category name."
    )
    user_prompt = f"User input: '{question}'"
    
    intent = get_llm_response(model_choice, system_prompt, user_prompt).strip().lower()
    
    if intent in ["greeting", "comparison", "summarization", "training_generation"]:
        return intent
    else:
        return "rag_query"

def handle_greeting(state):
    """
    Provides a direct response to a greeting.
    """
    return {**state, "answer": "Hello! How can I help you with the documents today?"}

def format_chat_history(chat_history: list) -> str:
    """Format chat history into a string."""
    return "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in chat_history])

def rewrite_question(state):
    """
    Rewrites the user's question and increments the rewrite counter.
    """
    question = state["question"]
    chat_history = state["chat_history"]
    model_choice = state["model_choice"]
    rewrite_count = state.get("rewrite_count", 0)

    # Increment rewrite counter
    rewrite_count += 1

    if not chat_history:
        return {**state, "question": question, "rewrite_count": rewrite_count}

    system_prompt = "You are a question rewriting expert."
    user_prompt = (
        "Given the following chat history and a follow-up question, "
        "rephrase the follow-up question to be a standalone question. "
        "Do not answer the question, just rewrite it."
        "\n\n"
        f"Chat History:\n{format_chat_history(chat_history)}\n"
        f"Follow-up Question: {question}\n"
        "Standalone question:"
    )
    
    rewritten_question = get_llm_response(model_choice, system_prompt, user_prompt)
    
    return {**state, "question": rewritten_question or question, "rewrite_count": rewrite_count}

def retrieve_context(state):
    """
    Retrieves context from the database based on the user's question.
    """
    question = state["question"]
    model_choice = state["model_choice"]
    max_chars = OCI_GENAI_CONTEXT_LIMIT_CHARS if model_choice == "OCI GenAI" else QWEN3_CONTEXT_LIMIT_CHARS

    conn = get_db_conn()
    if not conn:
        return {**state, "context": "", "citations": []}

    query = """
        WITH top_chunks AS (
          SELECT doc_id, chunk_id, chunk_data, VECTOR_DISTANCE(chunk_embedding, (VECTOR_EMBEDDING(ALL_MINILM_L12_V2 USING :query_text AS DATA))) AS distance
            FROM doc_chunks ORDER BY distance FETCH FIRST 25 ROWS ONLY ), ranked_docs AS (
            SELECT doc_id, COUNT(*) AS score FROM top_chunks GROUP BY doc_id ORDER BY score DESC FETCH FIRST 4 ROWS ONLY)
                SELECT tc.doc_id, ds.filename, tc.chunk_id, tc.chunk_data 
                FROM top_chunks tc 
                JOIN ranked_docs rd ON tc.doc_id = rd.doc_id 
                JOIN documentation_staging ds ON tc.doc_id = ds.id
                ORDER BY rd.score DESC, tc.distance
        """
    
    try:
        cursor = conn.cursor()
        cursor.execute(query, {'query_text': question})
        results = cursor.fetchall()
        context_parts, citations, current_length = [], set(), 0
        for doc_id, filename, chunk_id, chunk_data in results:
            part = f"Content: {chunk_data}\n\n"
            if current_length + len(part) > max_chars: 
                break
            context_parts.append(part)
            citations.add(f"`{filename}`")
            current_length += len(part)
        context = "".join(context_parts)
        cursor.close()
        conn.close()
    except Exception as e:
        st.error(f"Database retrieval failed: {e}")
        context, citations = "", []

    return {**state, "context": context, "citations": list(citations)}

def generate_answer(state):
    """
    Generates an answer using the retrieved context and chat history.
    """
    question = state["question"]
    context = state["context"]
    chat_history = state["chat_history"]
    model_choice = state["model_choice"]

    system_prompt = (
        "You are a helpful assistant. "
        "Answer the user's question based on the provided context and chat history. "
        "If the answer is not in the context, state that you could not find an answer in the provided documents."
    )
    user_prompt = (
        f"Context:\n{context}\n"
        f"Chat History:\n{format_chat_history(chat_history)}\n"
        f"Question: {question}\n"
        "Answer:"
    )

    answer = get_llm_response(model_choice, system_prompt, user_prompt, max_tokens=2000)
    
    # Preserve citations from the retrieval step
    citations = state.get("citations", [])
    
    return {**state, "answer": answer, "citations": citations}

def grade_context(state):
    """
    Determines whether the retrieved context is relevant and checks the rewrite limit.
    """
    rewrite_count = state.get("rewrite_count", 0)
    if rewrite_count > 1:
        return "give_up"

    question = state["question"]
    context = state["context"]
    model_choice = state["model_choice"]

    if not context:
        return "rewrite"

    system_prompt = (
        "You are a grader assessing the relevance of a retrieved context to a user question."
        "If the context contains information relevant to the question, respond with only the word 'yes'. "
        "Otherwise, respond with only the word 'no'."
    )
    user_prompt = (
        f"Retrieved Context:\n{context}\n\n"
        f"Question: {question}\n"
        "Is the context relevant to the question? (yes/no):"
    )
    
    score = get_llm_response(model_choice, system_prompt, user_prompt, max_tokens=10)
    
    if "yes" in score.lower():
        return "generate"
    else:
        return "rewrite"

def handle_give_up(state):
    """
    Provides a final response when the RAG pipeline cannot find an answer.
    """
    return {**state, "answer": "I'm sorry, but I was unable to find a relevant answer in the documents after several attempts."}

def deconstruct_query(state):
    """
    Deconstructs a comparison query into a list of sub-queries.
    """
    question = state["question"]
    model_choice = state["model_choice"]
    system_prompt = "You are an expert at deconstructing comparison questions."
    user_prompt = (
        "A user wants to compare things. Break their request into simple search queries. "
        "Return a JSON object with a single key 'plan' containing a list of strings."
        f"\n\nUser Request: \"{question}\""
    )
    
    response_str = get_llm_response(model_choice, system_prompt, user_prompt, json_mode=True, max_tokens=500)
    try:
        plan = json.loads(response_str).get("plan", [])
    except (json.JSONDecodeError, AttributeError):
        plan = []

    return {**state, "plan": plan}

def retrieve_for_comparison(state):
    """
    Retrieves context for each sub-query in the plan.
    """
    plan = state["plan"]
    model_choice = state["model_choice"]
    aggregated_context = {}
    all_citations = set()

    for sub_query in plan:
        # Reuse the existing retrieve_context logic for each sub-query
        retrieval_state = retrieve_context({"question": sub_query, "model_choice": model_choice})
        aggregated_context[sub_query] = retrieval_state.get("context", "")
        all_citations.update(retrieval_state.get("citations", []))

    return {**state, "aggregated_context": aggregated_context, "citations": list(all_citations)}

def synthesize_comparison(state):
    """
    Synthesizes a comparison answer from the aggregated context.
    """
    question = state["question"]
    aggregated_context = state["aggregated_context"]
    model_choice = state["model_choice"]

    system_prompt = "You are an expert analyst. Perform a detailed comparative analysis of the information provided."
    
    context_str = ""
    for sub_query, context in aggregated_context.items():
        context_str += f"--- Context for '{sub_query}' ---\n{context}\n\n"

    user_prompt = (
        f"User's Original Request: {question}\n\n"
        f"{context_str}"
        "--- Analysis Task ---\n"
        "Provide a comprehensive comparison based ONLY on the contexts above. "
        "Identify key similarities and differences. If information is missing for any part of the comparison, state that explicitly."
    )

    answer = get_llm_response(model_choice, system_prompt, user_prompt, max_tokens=1200)
    return {**state, "answer": answer}

def run_summarization(state):
    """
    Generates a summary of the retrieved context.
    """
    question = state["question"]
    context = state["context"]
    model_choice = state["model_choice"]

    system_prompt = "You are a document summarization expert."
    user_prompt = (
        "Based ONLY on the provided context, perform one of the following tasks:\n"
        "- If asked for a general summary, provide one under 300 words.\n"
        "- If asked to highlight specifics (e.g., workflows, roles), extract and list those key points.\n\n"
        f"Context:\n{context}\n\n"
        f"User's Request: \"{question}\"\n\n"
        "Generate the output now."
    )

    answer = get_llm_response(model_choice, system_prompt, user_prompt, max_tokens=1000)
    return {**state, "answer": answer}

def run_training_generation(state):
    """
    Generates training materials based on the retrieved context.
    """
    question = state["question"]
    context = state["context"]
    model_choice = state["model_choice"]

    system_prompt = "You are a corporate trainer and content creator."
    user_prompt = (
        "Based on the user's request, choose the MOST appropriate format below and generate the material using ONLY the provided context.\n\n"
        f"Context:\n{context}\n\n"
        f"User's Request: \"{question}\"\n\n"
        "**Formats:**\n"
        "- **Concise Summary**\n"
        "- **Slide-worthy Bullet Points**\n"
        "- **Scenario-based Quiz** (with answer key)\n"
        "- **Dos and Don'ts List**\n\n"
        "Generate the output now."
    )

    answer = get_llm_response(model_choice, system_prompt, user_prompt, max_tokens=1000)
    return {**state, "answer": answer}
