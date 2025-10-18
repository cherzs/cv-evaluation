from app.celery_app import celery
from app import create_app, db
from app.models.job import Job
from app.services.llm_pipeline import LLMPipeline
from datetime import datetime


@celery.task(bind=True, max_retries=3)
def evaluate_candidate(self, job_id: str):
    """
    Celery task to evaluate CV and project report
    
    Args:
        job_id: Job ID to process
        
    Returns:
        Evaluation results
    """
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        try:
            # Get job from database
            job = Job.query.get(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            # Update status to processing
            job.status = 'processing'
            job.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Initialize LLM pipeline
            llm_pipeline = LLMPipeline()
            
            # Run evaluation
            result = llm_pipeline.run_full_evaluation(
                cv_path=job.cv_path,
                project_path=job.report_path,
                job_title=job.job_title
            )
            
            # Update job with results
            job.status = 'completed'
            job.result = result
            job.updated_at = datetime.utcnow()
            db.session.commit()
            
            return result
            
        except Exception as e:
            # Handle failure
            error_message = str(e)
            print(f"Task failed for job {job_id}: {error_message}")
            
            # Update job status
            job = Job.query.get(job_id)
            if job:
                job.status = 'failed'
                job.error_message = error_message
                job.updated_at = datetime.utcnow()
                db.session.commit()
            
            # Retry if not max retries
            if self.request.retries < self.max_retries:
                raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
            
            raise


@celery.task
def seed_vector_store():
    """
    Task to seed vector store with initial data
    """
    from app.services.vector_store import VectorStoreService
    
    vector_store = VectorStoreService()
    vector_store.seed_initial_data()
    
    return {"status": "Vector store seeded successfully"}

