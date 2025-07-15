# RAG-Template v3 - Advanced RAG Application


> 📖 **Read the full project flow and deep dive in this blog post:**  
> [RAG-Template Flow (Notion)](https://vrajakishore.notion.site/RAG-Template-Flow-22a0931baa968075ac47cb371c789a28)

This project is an advanced, multi-modal Retrieval-Augmented Generation (RAG) application built with Streamlit, LangGraph, and Oracle 23ai. It provides a robust framework for building powerful, context-aware AI agents that can interact with a private knowledge base of documents.

The agent is designed to be modular and extensible, featuring a sophisticated graph-based architecture that can handle complex queries, including comparisons, summarizations, and dynamic question rewriting.

## 🚀 Features

- **Multi-Modal RAG Pipeline**: Leverages a graph-based workflow using LangGraph to intelligently handle different types of user queries.
- **Intent Classification**: Automatically classifies user intent to route queries to the appropriate workflow (e.g., simple Q&A, comparison, summarization).
- **Dynamic Question Rewriting**: Improves retrieval accuracy by rewriting user questions for better clarity and context.
- **Context Grading**: Evaluates the relevance of retrieved documents to ensure high-quality answers.
- **Pluggable LLM Support**: Easily switch between different Large Language Models (LLMs). Currently supports OCI GenAI and Qwen models.
- **Streamlit UI**: A user-friendly web interface for interacting with the agent, uploading documents, and managing prompts.
- **Document Ingestion**: A dedicated page for uploading and processing various file types (`.pdf`, `.docx`, `.csv`, etc.) into the knowledge base.
- **Document Summarization**: Generate and enhance summaries of ingested documents using a combination of Oracle's built-in functions and external LLMs.
- **Prompt Management**: A UI for creating, saving, and managing reusable prompt templates.
- **Dockerized**: Comes with a `Dockerfile` for easy setup and deployment.

## 🛠️ Tech Stack

- **Backend**: Python
- **Application Framework**: Streamlit
- **RAG & AI Orchestration**: LangChain, LangGraph
- **Database**: Oracle 23ai (for vector storage and retrieval)
- **LLMs**: OCI GenAI, Qwen
- **Cloud Services**: Oracle Cloud Infrastructure (OCI) for Object Storage
- **Deployment**: Docker

## ⚙️ Setup and Installation

### Prerequisites

- Docker installed on your machine.
- An Oracle Cloud Infrastructure (OCI) account with access to OCI GenAI and Object Storage.
- An Oracle 23ai Database instance.
- Credentials for an LLM provider (e.g., Qwen).

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd RAG-Template/RAG_template
```

### 2. Configure Environment Variables

Create a `.env` file by copying the example file:

```bash
cp .env.example .env
```

Now, edit the `.env` file and fill in the required values for your database, OCI services, and LLM endpoints.

### 3. Set Up OCI Configuration

This application uses the standard OCI configuration file to connect to OCI services. You need to create a `.oci` directory in the root of the project and place your configuration files inside it.

1.  **Create the directory**:
    ```bash
    mkdir .oci
    ```
2.  **Create `config` file**: Create a file named `.oci/config` with your OCI credentials. It should look like this:
    ```ini
    [DEFAULT]
    user=ocid1.user.oc1..xxxxxxxxxxxx
    fingerprint=xx:xx:xx:xx:xx:xx:xx:xx
    key_file=~/.oci/oci_api_key.pem
    tenancy=ocid1.tenancy.oc1..xxxxxxxxxxxx
    region=us-chicago-1
    ```
3.  **Add your API Key**: Place your OCI private key file at `.oci/oci_api_key.pem`.

**Important**: The `Dockerfile` copies the `.oci` directory into the container at `/root/.oci/`. Ensure the paths are correct.

### 4. Build and Run with Docker

Build the Docker image:

```bash
docker build -t rag-agent .
```

Run the Docker container:

```bash
docker run -p 8051:8051 -v $(pwd)/data:/app/data rag-agent
```

This command maps the container's port `8051` to your local machine and mounts a local `data` directory into the container to persist saved prompts.

### 5. Access the Application


Open your web browser and navigate to `http://localhost:8051`.

## 🔀 Model Selection & OCI GenAI Configuration

When using the application, you can select which LLM to use (Qwen or OCI GenAI) from the main chat interface. If you choose **OCI GenAI**, you must:

- Ensure the `.oci` directory and its configuration files are present as described above.
- The Dockerfile copies `.oci` into the container at `/root/.oci/`. This is required for OCI GenAI authentication.

**If you are NOT using OCI GenAI:**

- You do NOT need the `.oci` directory or its config files.
- You may comment out or remove the lines in the Dockerfile that copy `.oci` into the container:

```dockerfile
# COPY .oci /root/.oci/
```

This will prevent errors related to missing OCI credentials when only using Qwen or other non-OCI models.

## 📖 Usage

The application is divided into several pages, accessible from the sidebar navigation.

- **RAG-Template v3 (Main Chat)**: The main interface for interacting with the RAG agent. You can ask questions, and the agent will use the ingested documents to find answers. You can also select the LLM to use (Qwen or OCI GenAI).
- **Data Ingestion**: Upload new documents to the knowledge base. You can choose to append them to the existing base or perform a fresh ingestion, which will clear all previous data.
- **Document Summary**: Select an ingested document to generate a summary. The initial summary is created by Oracle 23ai, which can then be enhanced by the selected LLM.
- **Prompt Templates**: Create, view, edit, and delete prompt templates. This is useful for saving complex or frequently used prompts.

## 🌳 Project Structure

```
.
├── .oci/                  # OCI configuration directory
│   ├── config             # OCI config file
│   └── oci_api_key.pem    # OCI private key
├── core/                  # Core application logic
│   ├── graphs.py          # LangGraph RAG workflow definition
│   ├── nodes.py           # Nodes for the LangGraph workflow
│   ├── state.py           # Defines the state object for the graph
│   └── utils.py           # Utility functions (e.g., DB connection)
├── data/                  # Data directory (mounted via Docker)
│   └── saved_prompts/     # Saved prompt templates
├── pages/                 # Streamlit pages
│   ├── 1_Data_Ingestion.py
│   ├── 2_Document_Summary.py
│   └── 3_Prompt_Templates.py
├── .env                   # Your secret environment variables
├── .env.example           # Example environment variables
├── app.py                 # Main Streamlit application file
├── config.py              # Application configuration loader
├── Dockerfile             # Docker configuration for deployment
├── requirements.txt       # Python dependencies
└── README.md              # This file
```
