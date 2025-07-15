import streamlit as st
import os
import hashlib
import pandas as pd
import oci
import re
import time
from PyPDF2 import PdfReader
import zipfile
import xlrd
from core.utils import get_db_conn
from config import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
    BUCKET_NAME,
    NAMESPACE,
    OCI_CONFIG_PROFILE,
)

# --- OCI Configuration ---
try:
    config = oci.config.from_file(profile_name=OCI_CONFIG_PROFILE)
    object_storage = oci.object_storage.ObjectStorageClient(config)
except oci.exceptions.ConfigFileNotFound:
    st.error("OCI config file not found. Please ensure it is correctly set up.")
    st.stop()

# --- Helper Functions ---

def clean_filename(name):
    """Clean and standardize filename"""
    name = re.sub(r'[^\w\-.]', '_', name)
    if len(name) > 100:
        name = name[:95] + name[-5:]
    return name

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_hash(file):
    """Generate SHA-256 hash of file content"""
    file.seek(0)
    hash_val = hashlib.sha256(file.read()).hexdigest()
    file.seek(0)
    return hash_val

def validate_file_size(file):
    """Validate file size"""
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    return size <= MAX_FILE_SIZE, size

def is_duplicate(cursor, filename, filehash):
    """Check if file is already in database"""
    cursor.execute("""
        SELECT COUNT(*) FROM documentation_staging 
        WHERE filename = :fn OR file_hash = :fh
    """, {'fn': filename, 'fh': filehash})
    return cursor.fetchone()[0] > 0

def upload_file_to_oci(file, cleaned_name):
    """Uploads a file to OCI Object Storage with progress."""
    try:
        progress_bar = st.progress(0)
        object_storage.put_object(NAMESPACE, BUCKET_NAME, cleaned_name, file)
        progress_bar.progress(100)
        st.success(f"Successfully uploaded {cleaned_name} to OCI.")
        return True
    except Exception as e:
        st.error(f"Failed to upload {cleaned_name} to OCI: {e}")
        return False

# --- Main Streamlit App ---
st.set_page_config(page_title="Document Ingestion", page_icon="📚", layout="wide")
st.title("Document Ingestion")

st.markdown("Upload, validate, and process documents into the knowledge base.")

uploaded_files = st.file_uploader(
    "Choose files",
    type=list(ALLOWED_EXTENSIONS),
    accept_multiple_files=True,
    help="Upload documents to be processed into the RAG system."
)

if uploaded_files:
    st.markdown("### Ingestion Mode")
    mode = st.radio(
        "Choose ingestion mode:",
        ["Append to Existing", "Generate Fresh Knowledge Base"],
        help="Append adds new documents. Fresh clears all existing data first."
    )

    if st.button("🚀 Start Ingestion", type="primary"):
        validated_files = []
        for file in uploaded_files:
            cleaned_name = clean_filename(file.name)
            is_valid_size, size = validate_file_size(file)

            if not allowed_file(cleaned_name):
                st.warning(f"Skipped: Unsupported file type for '{cleaned_name}'")
                continue
            if not is_valid_size:
                st.warning(f"Skipped: File '{cleaned_name}' is too large ({size / 1024**2:.2f} MB).")
                continue
            
            validated_files.append((file, cleaned_name))

        if not validated_files:
            st.error("No valid files to process.")
            st.stop()

        conn = get_db_conn()
        if not conn:
            st.error("Database connection failed.")
            st.stop()
        
        cursor = conn.cursor()

        if mode == "Generate Fresh Knowledge Base":
            with st.spinner("Clearing existing knowledge base..."):
                cursor.execute("TRUNCATE TABLE doc_chunks")
                cursor.execute("TRUNCATE TABLE documentation_tab")
                cursor.execute("TRUNCATE TABLE documentation_staging")
                conn.commit()
                st.success("Knowledge base cleared.")

        with st.spinner("Processing files..."):
            for file, name in validated_files:
                file_hash = get_file_hash(file)
                if is_duplicate(cursor, name, file_hash):
                    st.info(f"Skipped duplicate file: {name}")
                    continue

                if upload_file_to_oci(file, name):
                    try:
                        cursor.execute(
                            "INSERT INTO documentation_staging (filename, file_hash) VALUES (:fn, :fh)",
                            {'fn': name, 'fh': file_hash}
                        )
                        conn.commit()
                        # Add logic here to trigger embedding and chunking if needed
                        st.success(f"Successfully staged '{name}' for processing.")
                    except Exception as e:
                        st.error(f"Database staging failed for '{name}': {e}")
                        conn.rollback()

        cursor.close()
        conn.close()
        st.balloons()
        st.success("Ingestion process complete!")