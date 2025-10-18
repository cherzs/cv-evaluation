import uuid
from datetime import datetime
from app import db


class Job(db.Model):
    """Job model for tracking evaluation tasks"""
    
    __tablename__ = 'jobs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_title = db.Column(db.String(255), nullable=False)
    cv_path = db.Column(db.String(500), nullable=False)
    report_path = db.Column(db.String(500), nullable=False)
    status = db.Column(
        db.String(50), 
        nullable=False, 
        default='queued'
    )  # queued, processing, completed, failed
    result = db.Column(db.JSON, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert job to dictionary"""
        return {
            'id': self.id,
            'job_title': self.job_title,
            'status': self.status,
            'result': self.result,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Job {self.id} - {self.status}>'

