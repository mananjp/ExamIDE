#!/bin/bash

# Update Nginx listen port based on environment variable (default 7860 for HF Spaces)
sed -i "s/listen 7860;/listen ${PORT:-7860};/g" /etc/nginx/nginx.conf

# Start the FastAPI backend in the background on localhost
cd /app/backend
uvicorn main:app --host 127.0.0.1 --port 8000 &

# Go back to /app
cd /app

# Start the Streamlit frontend in the background on localhost
streamlit run frontend/app.py \
    --server.port=8501 \
    --server.address=127.0.0.1 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false \
    --server.enableWebsocketCompression=false &

# Start Nginx in the foreground to keep the container alive
echo "Starting Nginx Proxy on port ${PORT:-7860}..."
nginx -g "daemon off;"
