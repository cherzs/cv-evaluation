# API Documentation

Complete API reference for the CV and Project Evaluation System.

**Powered by Google Gemini** - Fast and accurate AI evaluation!

## Base URL

```
http://localhost:5001/api
```

## Authentication

Currently, the API does not require authentication. For production use, implement JWT authentication.

## Common Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 202 | Accepted (job queued/processing) |
| 400 | Bad Request (validation error) |
| 404 | Not Found |
| 500 | Internal Server Error |

## Error Response Format

All errors follow this structure:

```json
{
  "error": "ErrorType",
  "message": "Detailed error message",
  "status_code": 400
}
```

---

## Endpoints

### 1. Health Check

Check API availability.

**Endpoint:** `GET /api/health`

**Response:**
```json
{
  "status": "healthy",
  "message": "CV Evaluation API is running"
}
```

---

### 2. Upload Files

Upload CV and project report PDFs.

**Endpoint:** `POST /api/upload`

**Content-Type:** `multipart/form-data`

**Request Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| cv | File (PDF) | Yes | Candidate's CV (max 10MB) |
| report | File (PDF) | Yes | Project report (max 10MB) |

**Success Response (200):**
```json
{
  "cv_id": "550e8400-e29b-41d4-a716-446655440000",
  "report_id": "650e8400-e29b-41d4-a716-446655440001",
  "message": "Files uploaded successfully"
}
```

**Error Responses:**

```json
// Missing CV
{
  "error": "ValidationError",
  "message": "CV file is required",
  "status_code": 400
}

// Invalid file type
{
  "error": "ValidationError",
  "message": "CV file error: File type not allowed. Allowed types: pdf",
  "status_code": 400
}

// File too large
{
  "error": "ValidationError",
  "message": "Report file error: File size exceeds maximum allowed size of 10.00MB",
  "status_code": 400
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:5001/api/upload \
  -F "cv=@/path/to/cv.pdf" \
  -F "report=@/path/to/report.pdf"
```

**Python Example:**
```python
import requests

files = {
    'cv': open('cv.pdf', 'rb'),
    'report': open('project_report.pdf', 'rb')
}

response = requests.post('http://localhost:5001/api/upload', files=files)
print(response.json())
```

---

### 3. Start Evaluation

Queue an evaluation job for processing.

**Endpoint:** `POST /api/evaluate`

**Content-Type:** `application/json`

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| job_title | String (1-255 chars) | Yes | Position title |
| cv_id | String (UUID) | Yes | CV ID from upload |
| report_id | String (UUID) | Yes | Report ID from upload |

```json
{
  "job_title": "Backend Developer",
  "cv_id": "550e8400-e29b-41d4-a716-446655440000",
  "report_id": "650e8400-e29b-41d4-a716-446655440001"
}
```

**Success Response (202):**
```json
{
  "job_id": "750e8400-e29b-41d4-a716-446655440002",
  "status": "queued",
  "message": "Evaluation job queued successfully"
}
```

**Error Responses:**

```json
// Missing request body
{
  "error": "ValidationError",
  "message": "Request body is required",
  "status_code": 400
}

// Invalid CV ID
{
  "error": "NotFoundError",
  "message": "CV file not found for ID: 550e8400-invalid-id",
  "status_code": 404
}

// Validation error
{
  "error": "ValidationError",
  "message": "1 validation error for EvaluateRequest\njob_title\n  Field required [type=missing, input_value={'cv_id': '123'}, input_type=dict]",
  "status_code": 400
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:5001/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "job_title": "Backend Developer",
    "cv_id": "550e8400-e29b-41d4-a716-446655440000",
    "report_id": "650e8400-e29b-41d4-a716-446655440001"
  }'
```

**Python Example:**
```python
import requests

data = {
    "job_title": "Backend Developer",
    "cv_id": "550e8400-e29b-41d4-a716-446655440000",
    "report_id": "650e8400-e29b-41d4-a716-446655440001"
}

response = requests.post(
    'http://localhost:5001/api/evaluate',
    json=data
)
print(response.json())
```

---

### 4. Get Evaluation Result

Retrieve evaluation results by job ID.

**Endpoint:** `GET /api/result/{job_id}`

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| job_id | String (UUID) | Job identifier |

**Response (Queued - 202):**
```json
{
  "id": "750e8400-e29b-41d4-a716-446655440002",
  "job_title": "Backend Developer",
  "status": "queued",
  "result": null,
  "error_message": null,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

**Response (Processing - 202):**
```json
{
  "id": "750e8400-e29b-41d4-a716-446655440002",
  "job_title": "Backend Developer",
  "status": "processing",
  "result": null,
  "error_message": null,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:15"
}
```

**Response (Completed - 200):**
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
      "cv_feedback": "The candidate demonstrates strong technical expertise in Python, Flask, and backend development. With 5 years of relevant experience, they show deep knowledge of the required technology stack. The CV highlights several impactful projects involving API development and system architecture. Cultural fit appears excellent based on collaborative projects and communication skills mentioned."
    },
    "project_evaluation": {
      "project_score": 4.25,
      "correctness_score": 5,
      "code_quality_score": 4,
      "resilience_score": 4,
      "documentation_score": 4,
      "project_feedback": "Excellent implementation of all required features. The API endpoints are properly designed and functional. Code is well-organized with good separation of concerns. Error handling is robust with retry mechanisms in place. Documentation is comprehensive with clear setup instructions and API examples. Minor improvement areas include adding more unit tests and optimizing some database queries."
    },
    "final_summary": "The candidate demonstrates strong technical skills with excellent problem-solving abilities. The CV shows relevant experience and achievements aligned with the Backend Developer position. The project submission is production-ready with proper architecture, error handling, and documentation. The candidate exhibits strong attention to detail and best practices.",
    "recommendation": "Highly Recommended",
    "overall_score": 4.1
  },
  "error_message": null,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:32:30"
}
```

**Response (Failed - 500):**
```json
{
  "id": "750e8400-e29b-41d4-a716-446655440002",
  "job_title": "Backend Developer",
  "status": "failed",
  "result": null,
  "error_message": "Error extracting text with PyMuPDF: file not found",
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:31:00"
}
```

**Error Response (404):**
```json
{
  "error": "NotFoundError",
  "message": "Job not found: 750e8400-invalid-id",
  "status_code": 404
}
```

**cURL Example:**
```bash
curl http://localhost:5001/api/result/750e8400-e29b-41d4-a716-446655440002
```

**Python Example with Polling:**
```python
import requests
import time

job_id = "750e8400-e29b-41d4-a716-446655440002"
url = f"http://localhost:5001/api/result/{job_id}"

while True:
    response = requests.get(url)
    data = response.json()
    
    status = data['status']
    print(f"Status: {status}")
    
    if status == 'completed':
        print("Evaluation completed!")
        print(f"Overall Score: {data['result']['overall_score']}")
        print(f"Recommendation: {data['result']['recommendation']}")
        break
    elif status == 'failed':
        print(f"Evaluation failed: {data['error_message']}")
        break
    
    time.sleep(5)  # Poll every 5 seconds
```

---

### 5. List Jobs

List all evaluation jobs with optional filtering.

**Endpoint:** `GET /api/jobs`

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| status | String | No | - | Filter by status: `queued`, `processing`, `completed`, `failed` |
| limit | Integer | No | 50 | Maximum results to return |

**Success Response (200):**
```json
{
  "jobs": [
    {
      "id": "750e8400-e29b-41d4-a716-446655440002",
      "job_title": "Backend Developer",
      "status": "completed",
      "result": { "..." },
      "error_message": null,
      "created_at": "2024-01-15T10:30:00",
      "updated_at": "2024-01-15T10:32:30"
    },
    {
      "id": "850e8400-e29b-41d4-a716-446655440003",
      "job_title": "Frontend Developer",
      "status": "processing",
      "result": null,
      "error_message": null,
      "created_at": "2024-01-15T11:00:00",
      "updated_at": "2024-01-15T11:00:15"
    }
  ],
  "count": 2
}
```

**cURL Examples:**
```bash
# Get all jobs
curl http://localhost:5001/api/jobs

# Get only completed jobs
curl "http://localhost:5001/api/jobs?status=completed"

# Get last 10 jobs
curl "http://localhost:5001/api/jobs?limit=10"

# Combine filters
curl "http://localhost:5001/api/jobs?status=completed&limit=5"
```

**Python Example:**
```python
import requests

# Get all completed jobs
response = requests.get(
    'http://localhost:5001/api/jobs',
    params={'status': 'completed', 'limit': 10}
)

data = response.json()
print(f"Found {data['count']} completed jobs")
for job in data['jobs']:
    print(f"- {job['job_title']}: {job['status']}")
```

---

## Data Models

### Job Status Values

- `queued`: Job created and waiting for processing
- `processing`: Job currently being evaluated
- `completed`: Job finished successfully
- `failed`: Job failed due to error

### Recommendation Values

- `Highly Recommended`: Overall score ≥ 4.0
- `Recommended`: Overall score 3.0-3.9
- `Maybe`: Overall score 2.0-2.9
- `Not Recommended`: Overall score < 2.0

### Score Ranges

- CV scores: 1-5 (integers)
- Project scores: 1-5 (integers)
- CV match rate: 0.0-1.0 (float)
- Project score: 0.0-5.0 (float)
- Overall score: 0.0-5.0 (float)

---

## Rate Limiting

Currently no rate limiting is implemented. For production, consider:

- 10 uploads per minute per IP
- 5 evaluation requests per minute per IP
- 60 result checks per minute per IP

---

## Best Practices

1. **Always validate file uploads** before sending
2. **Poll /result endpoint** every 5-10 seconds (don't spam)
3. **Handle all error responses** gracefully
4. **Store job_id** for later retrieval
5. **Implement timeout** for polling (e.g., 5 minutes max)
6. **Check file size** before upload (< 10MB)
7. **Use proper content types** for requests

---

## Postman Collection

Import this collection to test the API:

```json
{
  "info": {
    "name": "CV Evaluation API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/api/health"
      }
    },
    {
      "name": "Upload Files",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/api/upload",
        "body": {
          "mode": "formdata",
          "formdata": [
            {"key": "cv", "type": "file"},
            {"key": "report", "type": "file"}
          ]
        }
      }
    },
    {
      "name": "Start Evaluation",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/api/evaluate",
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"job_title\": \"Backend Developer\",\n  \"cv_id\": \"{{cv_id}}\",\n  \"report_id\": \"{{report_id}}\"\n}"
        }
      }
    },
    {
      "name": "Get Result",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/api/result/{{job_id}}"
      }
    },
    {
      "name": "List Jobs",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/api/jobs?status=completed&limit=10"
      }
    }
  ],
  "variable": [
    {"key": "base_url", "value": "http://localhost:5001"}
  ]
}
```

---

**Last Updated:** 2024-01-15

