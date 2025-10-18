#!/bin/bash
# Start Celery worker with solo pool (fixes ChromaDB multiprocessing issues)

echo "🚀 Starting Celery worker with solo pool..."
echo "📝 This fixes SIGSEGV errors with ChromaDB"
echo "🔕 Disabling ChromaDB telemetry"
echo ""

# Disable ChromaDB telemetry to avoid error messages
export ANONYMIZED_TELEMETRY=False

celery -A app.celery_app worker --pool=solo --loglevel=info

