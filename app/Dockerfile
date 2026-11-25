FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends fonts-dejavu-core && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir --default-timeout=120 --retries 10 "fastembed>=0.4" "psycopg[binary]>=3.2" "pgvector>=0.3" \
    "pypdf>=5" "python-docx>=1.1" "fpdf2>=2.8"
WORKDIR /app
COPY *.py *.json /app/
RUN python test_chunking.py
