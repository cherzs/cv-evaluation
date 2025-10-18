from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest
from app import db
from app.models.job import Job
from app.services.file_storage import FileStorageService
from app.api.schemas import (
    UploadResponse,
    EvaluateRequest,
    EvaluateResponse,
    JobStatus,
    ErrorResponse
)
from pydantic import ValidationError

# Create blueprint
api_bp = Blueprint('api', __name__)

# Initialize services
file_storage = FileStorageService()


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'CV Evaluation API is running'
    }), 200


@api_bp.route('/upload', methods=['POST'])
def upload_files():
    """
    Upload CV and Project Report
    
    Expects:
        - cv: PDF file (multipart/form-data)
        - report: PDF file (multipart/form-data)
    
    Returns:
        JSON with cv_id and report_id
    """
    try:
        # Check if files are present
        if 'cv' not in request.files:
            return jsonify({
                'error': 'ValidationError',
                'message': 'CV file is required',
                'status_code': 400
            }), 400
        
        if 'report' not in request.files:
            return jsonify({
                'error': 'ValidationError',
                'message': 'Project report file is required',
                'status_code': 400
            }), 400
        
        cv_file = request.files['cv']
        report_file = request.files['report']
        
        # Save CV
        try:
            cv_id, cv_path = file_storage.save_file(cv_file, prefix='cv')
        except ValueError as e:
            return jsonify({
                'error': 'ValidationError',
                'message': f'CV file error: {str(e)}',
                'status_code': 400
            }), 400
        
        # Save Report
        try:
            report_id, report_path = file_storage.save_file(report_file, prefix='report')
        except ValueError as e:
            # Clean up CV if report fails
            file_storage.delete_file(cv_path)
            return jsonify({
                'error': 'ValidationError',
                'message': f'Report file error: {str(e)}',
                'status_code': 400
            }), 400
        
        # Create response
        response = UploadResponse(
            cv_id=cv_id,
            report_id=report_id
        )
        
        return jsonify(response.model_dump()), 200
        
    except Exception as e:
        return jsonify({
            'error': 'InternalServerError',
            'message': str(e),
            'status_code': 500
        }), 500


@api_bp.route('/evaluate', methods=['POST'])
def evaluate():
    """
    Start evaluation job
    
    Expects:
        JSON body with:
        - job_title: str
        - cv_id: str
        - report_id: str
    
    Returns:
        JSON with job_id and status
    """
    try:
        # Parse and validate request
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'ValidationError',
                'message': 'Request body is required',
                'status_code': 400
            }), 400
        
        try:
            eval_request = EvaluateRequest(**data)
        except ValidationError as e:
            return jsonify({
                'error': 'ValidationError',
                'message': str(e),
                'status_code': 400
            }), 400
        
        # Build file paths from IDs (with correct prefixes)
        cv_path = file_storage.get_file_path(eval_request.cv_id, 'pdf', 'cv')
        report_path = file_storage.get_file_path(eval_request.report_id, 'pdf', 'report')
        
        # Check if files exist
        if not file_storage.file_exists(cv_path):
            return jsonify({
                'error': 'NotFoundError',
                'message': f'CV file not found for ID: {eval_request.cv_id}',
                'status_code': 404
            }), 404
        
        if not file_storage.file_exists(report_path):
            return jsonify({
                'error': 'NotFoundError',
                'message': f'Report file not found for ID: {eval_request.report_id}',
                'status_code': 404
            }), 404
        
        # Check for duplicate jobs (optional)
        existing_job = Job.query.filter_by(
            cv_path=cv_path,
            report_path=report_path,
            job_title=eval_request.job_title
        ).filter(Job.status.in_(['queued', 'processing', 'completed'])).first()
        
        if existing_job:
            return jsonify({
                'job_id': existing_job.id,
                'status': existing_job.status,
                'message': 'Job already exists for these files'
            }), 200
        
        # Create new job
        job = Job(
            job_title=eval_request.job_title,
            cv_path=cv_path,
            report_path=report_path,
            status='queued'
        )
        
        db.session.add(job)
        db.session.commit()
        
        # Queue evaluation task (import here to avoid circular import)
        from app.tasks import evaluate_candidate
        evaluate_candidate.delay(job.id)
        
        # Create response
        response = EvaluateResponse(
            job_id=job.id,
            status=job.status
        )
        
        return jsonify(response.model_dump()), 202
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'InternalServerError',
            'message': str(e),
            'status_code': 500
        }), 500


@api_bp.route('/result/<job_id>', methods=['GET'])
def get_result(job_id):
    """
    Get evaluation result by job ID
    
    Args:
        job_id: Job identifier
    
    Returns:
        JSON with job status and results (if completed)
    """
    try:
        # Get job from database
        job = Job.query.get(job_id)
        
        if not job:
            return jsonify({
                'error': 'NotFoundError',
                'message': f'Job not found: {job_id}',
                'status_code': 404
            }), 404
        
        # Return job status
        response = JobStatus(**job.to_dict())
        
        # Set appropriate status code based on job status
        status_code = 200
        if job.status == 'queued':
            status_code = 202  # Accepted, still processing
        elif job.status == 'processing':
            status_code = 202  # Accepted, still processing
        elif job.status == 'failed':
            status_code = 500  # Internal error
        
        return jsonify(response.model_dump()), status_code
        
    except Exception as e:
        return jsonify({
            'error': 'InternalServerError',
            'message': str(e),
            'status_code': 500
        }), 500


@api_bp.route('/jobs', methods=['GET'])
def list_jobs():
    """
    List all jobs (with optional filtering)
    
    Query params:
        - status: Filter by status (queued, processing, completed, failed)
        - limit: Limit number of results (default: 50)
    
    Returns:
        JSON array of jobs
    """
    try:
        # Get query parameters
        status = request.args.get('status')
        limit = request.args.get('limit', 50, type=int)
        
        # Build query
        query = Job.query
        
        if status:
            query = query.filter_by(status=status)
        
        # Order by created_at desc and limit
        jobs = query.order_by(Job.created_at.desc()).limit(limit).all()
        
        # Convert to dict
        jobs_data = [job.to_dict() for job in jobs]
        
        return jsonify({
            'jobs': jobs_data,
            'count': len(jobs_data)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'InternalServerError',
            'message': str(e),
            'status_code': 500
        }), 500


@api_bp.errorhandler(400)
def bad_request(e):
    """Handle 400 errors"""
    return jsonify({
        'error': 'BadRequest',
        'message': str(e),
        'status_code': 400
    }), 400


@api_bp.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({
        'error': 'NotFound',
        'message': str(e),
        'status_code': 404
    }), 404


@api_bp.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    return jsonify({
        'error': 'InternalServerError',
        'message': str(e),
        'status_code': 500
    }), 500

