# Multi-stage build for optimized unified (frontend + backend) deployment
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY frontend/requirements.txt requirements.txt
COPY backend/requirements.txt backend_requirements.txt

RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r backend_requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies for executing multi-language code and Nginx for routing
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    npm \
    g++ \
    default-jdk \
    dnsutils \
    curl \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application files
COPY frontend/ frontend/
COPY backend/ backend/
COPY start.sh start.sh
COPY nginx.conf /etc/nginx/nginx.conf

# Make start script executable
RUN chmod +x start.sh

# Expose the single proxy port (7860 for Hugging Face or Railway dynamic PORT)
EXPOSE 7860

# Proxy Configuration
ENV PORT=7860

# Run both Streamlit app and FastAPI using the wrapper script
CMD ["./start.sh"]
