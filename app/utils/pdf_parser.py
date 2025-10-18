import fitz  # PyMuPDF
import pdfplumber
from pathlib import Path
from typing import Optional


class PDFParser:
    """Utility class for parsing PDF files"""
    
    @staticmethod
    def extract_text_pymupdf(pdf_path: str) -> str:
        """
        Extract text from PDF using PyMuPDF
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        try:
            text_content = []
            with fitz.open(pdf_path) as doc:
                for page in doc:
                    text_content.append(page.get_text())
            return "\n".join(text_content)
        except Exception as e:
            raise Exception(f"Error extracting text with PyMuPDF: {str(e)}")
    
    @staticmethod
    def extract_text_pdfplumber(pdf_path: str) -> str:
        """
        Extract text from PDF using pdfplumber (better for tables)
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        try:
            text_content = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
            return "\n".join(text_content)
        except Exception as e:
            raise Exception(f"Error extracting text with pdfplumber: {str(e)}")
    
    @staticmethod
    def extract_text(pdf_path: str, method: str = 'pymupdf') -> str:
        """
        Extract text from PDF using specified method
        
        Args:
            pdf_path: Path to PDF file
            method: Extraction method ('pymupdf' or 'pdfplumber')
            
        Returns:
            Extracted text content
        """
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if method == 'pymupdf':
            return PDFParser.extract_text_pymupdf(pdf_path)
        elif method == 'pdfplumber':
            return PDFParser.extract_text_pdfplumber(pdf_path)
        else:
            raise ValueError(f"Invalid extraction method: {method}")
    
    @staticmethod
    def validate_pdf(pdf_path: str) -> bool:
        """
        Validate if file is a valid PDF
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            True if valid PDF, False otherwise
        """
        try:
            with fitz.open(pdf_path) as doc:
                return len(doc) > 0
        except:
            return False
    
    @staticmethod
    def get_page_count(pdf_path: str) -> int:
        """
        Get number of pages in PDF
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Number of pages
        """
        try:
            with fitz.open(pdf_path) as doc:
                return len(doc)
        except Exception as e:
            raise Exception(f"Error getting page count: {str(e)}")

