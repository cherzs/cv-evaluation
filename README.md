# CV and Project Evaluation System

A production-ready Flask backend service that evaluates CVs and project reports using LLM-powered analysis with RAG (Retrieval-Augmented Generation) pipeline.

## 🏗️ Architecture Overview

This system implements a sophisticated evaluation pipeline with:

- **Flask API**: RESTful endpoints for file upload, evaluation, and result retrieval
- **Celery + Redis**: Asynchronous job processing for long-running evaluations
- **ChromaDB**: Vector database for semantic search and RAG
- **Google Gemini**: AI-powered evaluation with structured scoring - FAST & ACCURATE
- **SQLite/PostgreSQL**: Job tracking and result storage
- **Docker**: Containerized deployment for easy scaling

### System Flow

```
1. User uploads CV + Project Report → /api/upload
2. Files stored with unique IDs → Returns cv_id, report_id
3. User triggers evaluation → /api/evaluate
4. Job queued in Celery → Returns job_id
5. Worker processes evaluation:
   - Extracts text from PDFs
   - Retrieves relevant context from vector DB
   - Evaluates CV (technical match, experience, etc.)
   - Evaluates project (code quality, documentation, etc.)
   - Generates final summary and recommendation
6. User polls for results → /api/result/{job_id}
7. Returns complete evaluation with scores
```

## 📁 Project Structure

```
Test-Backend/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── main.py                  # Application entry point
│   ├── celery_app.py            # Celery configuration
│   ├── tasks.py                 # Celery tasks
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py            # API endpoints
│   │   └── schemas.py           # Pydantic schemas
│   ├── models/
│   │   ├── __init__.py
│   │   └── job.py               # Job database model
│   ├── services/
│   │   ├── __init__.py
│   │   ├── file_storage.py      # File upload handling
│   │   ├── vector_store.py      # ChromaDB integration
│   │   └── llm_pipeline.py      # LLM evaluation logic
│   └── utils/
│       ├── __init__.py
│       └── pdf_parser.py        # PDF text extraction
├── scripts/
│   ├── init_db.py               # Database initialization
│   └── seed_vector_store.py     # Seed vector DB
├── tests/
│   ├── __init__.py
│   └── test_api.py              # API tests
├── config.py                    # Configuration
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Docker image
├── docker-compose.yml           # Multi-container setup
└── README.md                    # This file
```

## 🚀 Quick Start

### Option 1: Local Development (Recommended)

1. **Get Gemini API Key**
   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Copy the API key

2. **Configure Environment**
   ```bash
   # Copy the example environment file
   cp env.example .env
   
   # Edit .env and add your API key
   GEMINI_API_KEY=your-api-key-here
   ```

3. **Install Python dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Initialize Database**
   ```bash
   python -c "from app import create_app; from app.models import db; app = create_app(); app.app_context().push(); db.create_all()"
   ```

5. **Seed Vector Store**
   ```bash
   python -c "from app.services.vector_store import VectorStoreService; vs = VectorStoreService(); vs.seed_initial_data()"
   ```


6. **Start Redis** (Terminal 3)
   ```bash
   # macOS: brew install redis
   redis-server
   ```

7. **Start Flask API** (Terminal 4)
   ```bash
   python app/main.py
   ```

8. **Start Celery worker** (Terminal 5)
   ```bash
   # Use solo pool to avoid multiprocessing issues
   celery -A app.celery_app worker --pool=solo --loglevel=info
   ```

9. **API is ready at `http://localhost:5001`** 🎉

### Option 2: Docker Setup

1. **Configure Environment**
   ```bash
   # Copy the example environment file
   cp env.example .env
   
   # Edit .env and add your Gemini API key
   GEMINI_API_KEY=your-api-key-here
   ```

2. **Start containers**
   ```bash
   docker-compose up -d
   ```

3. **Seed vector store**
   ```bash
   docker-compose exec api python -c "from app.services.vector_store import VectorStoreService; vs = VectorStoreService(); vs.seed_initial_data()"
   ```

## 📡 API Endpoints

### 1. Health Check

**GET** `/api/health`

Check if API is running.

**Response:**
```json
{
  "status": "healthy",
  "message": "CV Evaluation API is running"
}
```

### 2. Upload Files

**POST** `/api/upload`

Upload CV and project report PDFs.

**Request:**
- Content-Type: `multipart/form-data`
- Fields:
  - `cv`: PDF file (max 10MB)
  - `report`: PDF file (max 10MB)

**Response:**
```json
{
  "cv_id": "550e8400-e29b-41d4-a716-446655440000",
  "report_id": "650e8400-e29b-41d4-a716-446655440001",
  "message": "Files uploaded successfully"
}
```

**Example:**
```bash
curl -X POST http://localhost:5001/api/upload \
  -F "cv=@/path/to/cv.pdf" \
  -F "report=@/path/to/project_report.pdf"
```

### 3. Start Evaluation

**POST** `/api/evaluate`

Queue an evaluation job.

**Request Body:**
```json
{
  "job_title": "Backend Developer",
  "cv_id": "550e8400-e29b-41d4-a716-446655440000",
  "report_id": "650e8400-e29b-41d4-a716-446655440001"
}
```

**Response:**
```json
{
  "job_id": "750e8400-e29b-41d4-a716-446655440002",
  "status": "queued",
  "message": "Evaluation job queued successfully"
}
```

**Example:**
```bash
curl -X POST http://localhost:5001/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "job_title": "Backend Developer",
    "cv_id": "550e8400-e29b-41d4-a716-446655440000",
    "report_id": "650e8400-e29b-41d4-a716-446655440001"
  }'
```

### 4. Get Evaluation Result

**GET** `/api/result/{job_id}`

Retrieve evaluation results.

**Response (Processing):**
```json
{
  "id": "750e8400-e29b-41d4-a716-446655440002",
  "job_title": "Backend Developer",
  "status": "processing",
  "result": null,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:15"
}
```

**Response (Completed):**
```json
{
  "id": "750e8400-e29b-41d4-a716-446655440002",
  "job_title": "Backend Developer",
  "status": "completed",
  "result": {
    "cv_evaluation": {
      "cv_match_rate": 0.82,
      "technical_match": 4,
      "experience_score": 4,
      "achievements_score": 3,
      "cultural_fit_score": 5,
      "cv_feedback": "Strong technical background with 5 years of Python experience..."
    },
    "project_evaluation": {
      "project_score": 4.25,
      "correctness_score": 5,
      "code_quality_score": 4,
      "resilience_score": 4,
      "documentation_score": 4,
      "project_feedback": "Excellent implementation of all requirements..."
    },
    "final_summary": "The candidate demonstrates strong technical skills and excellent problem-solving abilities. The project submission shows production-ready code with proper error handling and documentation.",
    "recommendation": "Highly Recommended",
    "overall_score": 4.1
  },
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:32:30"
}
```

**Example:**
```bash
curl http://localhost:5001/api/result/750e8400-e29b-41d4-a716-446655440002
```

### 5. List Jobs

**GET** `/api/jobs?status=completed&limit=10`

List all jobs with optional filtering.

**Query Parameters:**
- `status` (optional): Filter by status (`queued`, `processing`, `completed`, `failed`)
- `limit` (optional): Max results (default: 50)

**Response:**
```json
{
  "jobs": [
    {
      "id": "750e8400-e29b-41d4-a716-446655440002",
      "job_title": "Backend Developer",
      "status": "completed",
      "created_at": "2024-01-15T10:30:00"
    }
  ],
  "count": 1
}
```

## 🧪 Testing

Run tests with pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_api.py -v
```

## 🔧 Configuration

All configuration is managed through environment variables in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Environment (development/production) | development |
| `SECRET_KEY` | Flask secret key | (random) |
| `DATABASE_URL` | Database connection string | sqlite:///./app.db |
| `REDIS_URL` | Redis connection string | redis://localhost:6379/0 |
| `GEMINI_API_KEY` | Google Gemini API key | (required) |
| `GEMINI_MODEL` | Gemini model name | gemini-2.0-flash |
| `GEMINI_TEMPERATURE` | LLM temperature | 0.3 |
| `UPLOAD_FOLDER` | Upload directory | ./uploads |
| `MAX_FILE_SIZE` | Max file size in bytes | 10485760 (10MB) |

## 📊 Evaluation Rubrics

### CV Evaluation (1-5 scale each)

1. **Technical Match**: Required skills coverage, technology stack alignment
2. **Experience Score**: Years of relevant experience, project complexity
3. **Achievements Score**: Quantifiable accomplishments, awards, contributions
4. **Cultural Fit Score**: Communication skills, team collaboration

**CV Match Rate** = Average of all scores / 5

### Project Evaluation (1-5 scale each)

1. **Correctness Score**: All requirements met, proper implementation
2. **Code Quality Score**: Clean code, good architecture, organization
3. **Resilience Score**: Error handling, retry mechanisms, edge cases
4. **Documentation Score**: README, API docs, code comments

**Project Score** = Average of all scores

### Final Recommendation

- **Highly Recommended**: Overall score ≥ 4.0
- **Recommended**: Overall score 3.0-3.9
- **Maybe**: Overall score 2.0-2.9
- **Not Recommended**: Overall score < 2.0

## 🔥 Error Handling

The system implements comprehensive error handling:

- **Retry Logic**: LLM calls retry up to 3x with exponential backoff
- **Validation**: File type, size, and format validation
- **Graceful Degradation**: Fallback to cached rubric if vector DB fails
- **Job Tracking**: Failed jobs marked with error messages
- **HTTP Status Codes**: Proper error responses with details

## 💰 Why Gemini?

Google Gemini provides **fast and accurate AI evaluation**:

✅ **High Quality** - Advanced AI model with excellent reasoning  
✅ **Fast Processing** - Quick response times for evaluations  
✅ **Reliable** - Google's robust infrastructure  
✅ **Easy Integration** - Simple API with good documentation  
✅ **Cost Effective** - Competitive pricing for API usage  
✅ **Scalable** - Handles high volume evaluations  

**Model Used:**
- `gemini-2.0-flash` - Fast, accurate model for evaluation tasks

## 🚦 Production Deployment

### Docker Production Setup

1. **Update docker-compose.yml** to use PostgreSQL:
   ```yaml
   # Uncomment postgres service and update DATABASE_URL
   ```

2. **Set production environment variables**:
   ```bash
   FLASK_ENV=production
   SECRET_KEY=<strong-random-key>
   ```

3. **Deploy**:
   ```bash
   docker-compose -f docker-compose.yml up -d
   ```

### Environment Variables for Production

- Use **strong SECRET_KEY**
- Use **PostgreSQL** instead of SQLite
- Set **FLASK_ENV=production**
- Configure proper **logging**
- Enable **rate limiting** on API endpoints
- Set up **monitoring** (Sentry, DataDog, etc.)

## 🛠️ Development

### Code Quality

```bash
# Format code
black app/ tests/

# Lint
flake8 app/ tests/
```

### Adding New Evaluation Criteria

1. Update vector store seeds in `app/services/vector_store.py`
2. Modify LLM prompts in `app/services/llm_pipeline.py`
3. Update schemas in `app/api/schemas.py`
4. Re-seed vector store

## 📝 License

This project is part of a technical assessment for backend developer position.

## 🤝 Support

For issues or questions, please contact the development team.

---

**Built with ❤️ using Flask, Celery, ChromaDB, and Google Gemini**

