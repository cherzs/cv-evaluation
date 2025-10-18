"""API endpoint tests"""
import pytest
import json
from app import create_app, db


@pytest.fixture
def app():
    """Create test app"""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'


def test_upload_missing_files(client):
    """Test upload endpoint with missing files"""
    response = client.post('/api/upload')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data


def test_evaluate_missing_body(client):
    """Test evaluate endpoint with missing body"""
    response = client.post('/api/evaluate')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data


def test_get_result_not_found(client):
    """Test get result with non-existent job"""
    response = client.get('/api/result/nonexistent-job-id')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data


def test_list_jobs(client):
    """Test list jobs endpoint"""
    response = client.get('/api/jobs')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'jobs' in data
    assert 'count' in data

