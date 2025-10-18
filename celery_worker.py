"""Celery worker entry point"""
from app.celery_app import celery
from app.tasks import evaluate_candidate, seed_vector_store  # Import tasks explicitly

# Import Flask app to ensure database context
from app.main import app

if __name__ == '__main__':
    with app.app_context():
        celery.start()
