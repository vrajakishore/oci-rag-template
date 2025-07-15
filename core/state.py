from typing import List, TypedDict

class RAGState(TypedDict):
    """
    Represents the state of the RAG workflow.

    Attributes:
        question (str): The initial question from the user.
        chat_history (list): The history of the conversation.
        context (str): The retrieved context from the vector store.
        answer (str): The generated answer from the LLM.
        citations (list): A list of source documents for the answer.
        rewrite_count (int): A counter for how many times the question has been rewritten.
        plan (list): A list of sub-queries for comparison tasks.
        aggregated_context (dict): Aggregated context for comparison tasks.
        model_choice (str): The language model selected by the user.
    """
    question: str
    chat_history: list
    context: str
    answer: str
    citations: List[str]
    rewrite_count: int
    plan: List[str]
    aggregated_context: dict
    model_choice: str