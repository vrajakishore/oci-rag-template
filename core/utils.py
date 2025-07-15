import oracledb
import streamlit as st
from config import DB_USER, DB_PASSWORD, DB_DSN

# Oracle client initialization
try:
    oracledb.init_oracle_client(lib_dir="/app/oracle-client/instantclient_23_8")
except Exception as e:
    print(f"Oracle client init warning: {e}")

def get_db_conn():
    """Get database connection with error handling"""
    try:
        return oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN)
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None
