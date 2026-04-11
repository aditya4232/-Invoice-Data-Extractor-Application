# ============================================================
# Invoice Data Extractor - Dockerfile
# Production-ready Docker image for Streamlit deployment
# ============================================================

FROM python:3.11-slim

LABEL maintainer="Invoice Data Extractor"
LABEL description="India-specific invoice OCR extractor using Tesseract with ML-based training"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Tesseract OCR dependencies
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-hin \
    # Hindi and other Indian languages support
    tesseract-ocr-script-deva \
    # Image processing libraries
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    # Poppler for PDF support
    poppler-utils \
    # Additional utilities
    wget \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/sample_invoices /app/output /app/models /app/annotations

# Set environment variables for Tesseract
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
