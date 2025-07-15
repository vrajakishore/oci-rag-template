import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Database Configuration ---
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("PYTHON_PASSWORD")
DB_HOSTNAME = os.getenv("DB_HOSTNAME")
DB_SERVICE_NAME = os.getenv("SERVICE_NAME")
DB_DSN = f"{DB_HOSTNAME}:1521/{DB_SERVICE_NAME}"
PAGES_DB_DSN = os.getenv("PAGES_DB_DSN")

# --- OCI Configuration ---
OCI_CONFIG_PROFILE = os.getenv("OCI_CONFIG_PROFILE", "DEFAULT")
OCI_AUTH_TYPE = os.getenv("OCI_AUTH_TYPE", "API_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")
COMPARTMENT_ID = os.getenv("COMPARTMENT_ID")
NAMESPACE = os.getenv("NAMESPACE")

# --- Qwen3 Configuration ---
QWEN_ENDPOINT = os.getenv("QWEN_ENDPOINT")
#format "https://api.qwen3.com/v1/chat/completions"

# --- OCI GenAI Configuration ---
GENAI_ENDPOINT = os.getenv("GENAI_ENDPOINT")
GENAI_MODEL_ID = os.getenv("GENAI_MODEL_ID")
GENAI_COMPARTMENT_ID = os.getenv("GENAI_COMPARTMENT_ID")


# --- Application Configuration ---
QWEN3_CONTEXT_LIMIT_CHARS = int(os.getenv("QWEN3_CONTEXT_LIMIT_CHARS", 16000))
OCI_GENAI_CONTEXT_LIMIT_CHARS = int(os.getenv("OCI_GENAI_CONTEXT_LIMIT_CHARS", 30000))

# --- Data Ingestion Configuration ---
ALLOWED_EXTENSIONS = {"pdf", "csv", "xls", "xlsx", "ppt", "pptx", "txt", "md", "html", "json", "docx", "doc"}
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE_MB", 100)) * 1024 * 1024
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 8192))
PAR_BASE_URL = os.getenv("BUCKET_PAR")
PAR_READ_URL = os.getenv("PAR_READ_URL")
