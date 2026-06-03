#!/bin/bash
# Build ChromaDB if it doesn't exist
if [ ! -d "db" ] || [ -z "$(ls -A db)" ]; then
    echo "Building vector database..."
    python build_db.py
fi
echo "Starting API..."
uvicorn api:app --host 0.0.0.0 --port $PORT
