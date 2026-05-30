FROM python:3.10-slim

# System dependencies for PyMuPDF, lxml, and torch OpenMP
RUN apt-get update && apt-get install -y --no-install-recommends \
        libglib2.0-0 \
        libgomp1 \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install CPU-only torch first (avoids pulling 2 GB CUDA wheel by accident)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install remaining Python dependencies
COPY environment.yml /tmp/environment.yml
RUN pip install --no-cache-dir \
        "transformers>=4.46.3,<5.0.0" \
        sentencepiece \
        accelerate \
        fastapi \
        "uvicorn[standard]" \
        pydantic \
        pydantic-settings \
        python-multipart \
        python-dotenv \
        httpx \
        numpy \
        pandas \
        scikit-learn \
        nltk \
        regex \
        tqdm \
        pyyaml \
        rouge-score \
        underthesea \
        pyvi \
        pymupdf \
        python-docx \
        beautifulsoup4 \
        lxml \
        "chardet==5.2.0"

# Copy application source
COPY app/ ./app/
COPY run_api.py ./run_api.py

# Expose API port (overridable via API_PORT env var)
EXPOSE 8000

# HuggingFace model cache — mount from host at runtime
# docker run -v ~/.cache/huggingface:/root/.cache/huggingface ...
ENV HF_DATASETS_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1

# Bind to 0.0.0.0 so the container port is reachable from outside
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
