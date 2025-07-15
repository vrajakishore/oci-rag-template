from langgraph.graph import END, StateGraph
from core.state import RAGState
from core.nodes import (
    rewrite_question,
    retrieve_context,
    generate_answer,
    grade_context,
    classify_intent,
    handle_greeting,
    handle_give_up,
    deconstruct_query,
    retrieve_for_comparison,
    synthesize_comparison,
    run_summarization,
    run_training_generation,
)

def create_rag_graph():
    """
    Creates and compiles the LangGraph workflow for the RAG application.
    """
    workflow = StateGraph(RAGState)

    # Add nodes to the graph
    workflow.add_node("rewrite_question", rewrite_question)
    workflow.add_node("retrieve_context", retrieve_context)
    workflow.add_node("generate_answer", generate_answer)
    workflow.add_node("handle_greeting", handle_greeting)
    workflow.add_node("handle_give_up", handle_give_up)
    workflow.add_node("deconstruct_query", deconstruct_query)
    workflow.add_node("retrieve_for_comparison", retrieve_for_comparison)
    workflow.add_node("synthesize_comparison", synthesize_comparison)
    workflow.add_node("run_summarization", run_summarization)
    workflow.add_node("run_training_generation", run_training_generation)


    # Set the entry point
    workflow.set_conditional_entry_point(
        classify_intent,
        {
            "greeting": "handle_greeting",
            "rag_query": "rewrite_question",
            "comparison": "deconstruct_query",
            "summarization": "retrieve_context",
            "training_generation": "retrieve_context",
        },
    )

    # Add edges for the general RAG workflow
    workflow.add_edge("rewrite_question", "retrieve_context")
    workflow.add_conditional_edges(
        "retrieve_context",
        grade_context,
        {
            "generate": "generate_answer",
            "rewrite": "rewrite_question",
            "give_up": "handle_give_up",
        },
    )
    
    # Add edges for the comparison workflow
    workflow.add_edge("deconstruct_query", "retrieve_for_comparison")
    workflow.add_edge("retrieve_for_comparison", "synthesize_comparison")
    workflow.add_edge("synthesize_comparison", END)

    # Add edges for summarization and training generation
    workflow.add_edge("run_summarization", END)
    workflow.add_edge("run_training_generation", END)


    workflow.add_edge("generate_answer", END)
    workflow.add_edge("handle_greeting", END)
    workflow.add_edge("handle_give_up", END)

    # Compile the graph
    app = workflow.compile()
    return app
