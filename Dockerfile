# Install system dependencies
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y libgl1 libglib2.0-0 libaio1 wget unzip vim curl build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Oracle Instant Client
RUN mkdir -p /app/oracle-client && \
    cd /app/oracle-client && \
    wget https://download.oracle.com/otn_software/linux/instantclient/2380000/instantclient-basic-linux.x64-23.8.0.25.04.zip && \
    unzip instantclient-basic-linux.x64-23.8.0.25.04.zip && \
    rm instantclient-basic-linux.x64-23.8.0.25.04.zip && \
    ln -s instantclient_23_8 instantclient

# Set environment variables for Oracle Instant Client
ENV LD_LIBRARY_PATH=/app/oracle-client/instantclient_23_8
ENV PATH=/app/oracle-client/instantclient_23_8:$PATH

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# OCI config
RUN mkdir -p /root/.oci
COPY .oci/config /root/.oci/config
COPY .oci/oci_api_key.pem /root/.oci/oci_api_key.pem
RUN chmod 600 /root/.oci/oci_api_key.pem
ENV OCI_CONFIG_FILE=/root/.oci/config

# Copy app code
RUN mkdir -p /app/data/saved_prompts
COPY . .

# Expose the port that Streamlit will use 
EXPOSE 8051

# Run Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8051", "--server.address=0.0.0.0"]
