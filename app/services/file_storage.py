import os
import uuid
from pathlib import Path
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from typing import Tuple, Optional
from config import Config


class FileStorageService:
    """Service for handling file uploads and storage"""
    
    def __init__(self, upload_folder: str = None):
        self.upload_folder = upload_folder or Config.UPLOAD_FOLDER
        self.max_file_size = Config.MAX_FILE_SIZE
        self.allowed_extensions = Config.ALLOWED_EXTENSIONS
        
        # Ensure upload directory exists
        os.makedirs(self.upload_folder, exist_ok=True)
    
    def allowed_file(self, filename: str) -> bool:
        """
        Check if file extension is allowed
        
        Args:
            filename: Name of the file
            
        Returns:
            True if allowed, False otherwise
        """
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def validate_file(self, file: FileStorage) -> Tuple[bool, Optional[str]]:
        """
        Validate uploaded file
        
        Args:
            file: Uploaded file object
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file:
            return False, "No file provided"
        
        if file.filename == '':
            return False, "No file selected"
        
        if not self.allowed_file(file.filename):
            return False, f"File type not allowed. Allowed types: {', '.join(self.allowed_extensions)}"
        
        # Check file size (read first chunk to estimate)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > self.max_file_size:
            return False, f"File size exceeds maximum allowed size of {self.max_file_size / (1024*1024):.2f}MB"
        
        return True, None
    
    def save_file(self, file: FileStorage, prefix: str = '') -> Tuple[str, str]:
        """
        Save uploaded file with unique identifier
        
        Args:
            file: Uploaded file object
            prefix: Optional prefix for filename
            
        Returns:
            Tuple of (file_id, file_path)
        """
        # Validate file first
        is_valid, error_msg = self.validate_file(file)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        
        # Secure the filename and add unique ID
        original_filename = secure_filename(file.filename)
        extension = original_filename.rsplit('.', 1)[1].lower()
        
        # Create filename with prefix and ID
        if prefix:
            filename = f"{prefix}_{file_id}.{extension}"
        else:
            filename = f"{file_id}.{extension}"
        
        # Save file
        file_path = os.path.join(self.upload_folder, filename)
        file.save(file_path)
        
        return file_id, file_path
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from storage
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False
    
    def file_exists(self, file_path: str) -> bool:
        """
        Check if file exists
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if exists, False otherwise
        """
        return os.path.exists(file_path)
    
    def get_file_path(self, file_id: str, extension: str = 'pdf', prefix: str = '') -> str:
        """
        Get full path for a file ID
        
        Args:
            file_id: Unique file identifier
            extension: File extension
            prefix: Optional prefix for filename
            
        Returns:
            Full file path
        """
        if prefix:
            filename = f"{prefix}_{file_id}.{extension}"
        else:
            filename = f"{file_id}.{extension}"
        return os.path.join(self.upload_folder, filename)

