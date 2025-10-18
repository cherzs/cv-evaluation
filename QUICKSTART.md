# ⚡ Quick Start Guide

Get the CV Evaluation System running in 5 minutes!

## Prerequisites

- Python 3.9+
- Redis (for job queue)
- Google Gemini API Key

## Step-by-Step Setup

### 1️⃣ Get Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the API key (you'll need it in step 3)

### 2️⃣ Install Python Dependencies

```bash
cd Test-Backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 3️⃣ Create Environment File

```bash
cat > .env << 'EOF'
FLASK_ENV=development
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-2.0-flash
GEMINI_TEMPERATURE=0.3
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=sqlite:///./app.db
UPLOAD_FOLDER=./uploads
MAX_FILE_SIZE=10485760
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
SECRET_KEY=your-secret-key-change-this
ANONYMIZED_TELEMETRY=False
EOF
```

**Important:** Replace `your-gemini-api-key-here` with your actual Gemini API key!

### 4️⃣ Initialize Database & Vector Store

```bash
# Create database
python -c "from app import create_app; from app.models import db; app = create_app(); app.app_context().push(); db.create_all()"

# Seed vector store with evaluation rubrics
python -c "from app.services.vector_store import VectorStoreService; vs = VectorStoreService(); vs.seed_initial_data()"
```

### 5️⃣ Start Redis

Open **Terminal 1**:
```bash
# macOS
brew install redis
redis-server

# Linux
sudo apt-get install redis
redis-server

# Windows - Download from:
# https://github.com/microsoftarchive/redis/releases
```

### 6️⃣ Start Flask API

Open **Terminal 2**:
```bash
source venv/bin/activate  # If not already activated
python app/main.py
```

You should see:
```
 * Running on http://0.0.0.0:5001
```

### 7️⃣ Start Celery Worker

Open **Terminal 3**:
```bash
source venv/bin/activate
# Use solo pool to avoid multiprocessing issues with ChromaDB
celery -A app.celery_app worker --pool=solo --loglevel=info
```

**Note:** We use `--pool=solo` because ChromaDB doesn't work well with Celery's default multiprocessing (fork) pool on macOS.

## 🎉 Test It!

### Health Check

```bash
curl http://localhost:5001/api/health
```

Expected output:
```json
{
  "status": "healthy",
  "message": "CV Evaluation API is running"
}
```

### Full Test (with sample files)

```bash
# Upload files
curl -X POST http://localhost:5001/api/upload \
  -F "cv=@/path/to/sample_cv.pdf" \
  -F "report=@/path/to/sample_report.pdf"

# Response:
# {
#   "cv_id": "abc123...",
#   "report_id": "def456..."
# }

# Start evaluation
curl -X POST http://localhost:5001/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "job_title": "Backend Developer",
    "cv_id": "abc123...",
    "report_id": "def456..."
  }'

# Response:
# {
#   "job_id": "xyz789...",
#   "status": "queued"
# }

# Check results (wait ~30-60 seconds)
curl http://localhost:5001/api/result/xyz789...
```

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'google.generativeai'"

```bash
# Activate venv first
source venv/bin/activate

# Then reinstall
pip install google-generativeai
```

### Celery worker not starting

```bash
# Make sure Redis is running
redis-cli ping
# Should return: PONG

# Check Redis is on correct port
netstat -an | grep 6379
```

### Gemini API errors

```bash
# Check your API key is correct in .env file
cat .env | grep GEMINI_API_KEY

# Test API key manually
python -c "import google.generativeai as genai; genai.configure(api_key='your-key'); print('API key works!')"
```

## 📝 Summary of Running Services

You should have 3 terminals running:

1. **Redis** - `redis-server`
2. **Flask API** - `python app/main.py`
3. **Celery Worker** - `celery -A app.celery_app worker --pool=solo --loglevel=info`

## 🔄 Daily Usage

After initial setup, to start the system:

```bash
# Terminal 1
redis-server

# Terminal 2
cd Test-Backend
source venv/bin/activate
python app/main.py

# Terminal 3
cd Test-Backend
source venv/bin/activate
celery -A app.celery_app worker --pool=solo --loglevel=info
```

## 🎯 Next Steps

- Read [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for API details
- Check [README.md](README.md) for advanced features
- Try the web interface at `http://localhost:5001`

---

**Need help?** Check the main README or open an issue!