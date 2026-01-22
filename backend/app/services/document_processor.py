"""
Document processing service for PDF, DOCX, and TXT files
"""
import os
from abc import ABC, abstractmethod
from typing import Optional
import chardet
import PyPDF2
import pdfplumber
from docx import Document as DocxDocument


class DocumentParser(ABC):
    """Abstract base class for document parsers"""
    
    @abstractmethod
    def parse(self, file_path: str) -> str:
        """Parse document and return text"""
        pass


class PDFParser(DocumentParser):
    """PDF document parser with fallback strategies"""
    
    def parse(self, file_path: str) -> str:
        """Parse PDF using PyPDF2 with pdfplumber fallback"""
        text = ""
        
        # Try PyPDF2 first
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            # If PyPDF2 got good results, return
            if len(text.strip()) > 100:
                return text
        except Exception as e:
            print(f"PyPDF2 failed: {e}, trying pdfplumber...")
        
        # Fallback to pdfplumber
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            raise ValueError(f"Failed to parse PDF: {e}")
        
        if not text.strip():
            raise ValueError("No text extracted from PDF. File may be scanned or corrupted.")
        
        return text


class DOCXParser(DocumentParser):
    """DOCX document parser"""
    
    def parse(self, file_path: str) -> str:
        """Parse DOCX file"""
        try:
            doc = DocxDocument(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            
            if not text.strip():
                raise ValueError("No text found in DOCX file")
            
            return text
        except Exception as e:
            raise ValueError(f"Failed to parse DOCX: {e}")


class TextParser(DocumentParser):
    """Plain text parser with encoding detection"""
    
    def parse(self, file_path: str) -> str:
        """Parse text file with automatic encoding detection"""
        try:
            # Detect encoding
            with open(file_path, 'rb') as file:
                raw_data = file.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding'] or 'utf-8'
            
            # Read with detected encoding
            with open(file_path, 'r', encoding=encoding) as file:
                text = file.read()
            
            if not text.strip():
                raise ValueError("Text file is empty")
            
            return text
        except Exception as e:
            raise ValueError(f"Failed to parse text file: {e}")


class DocumentProcessor:
    """Main document processor that orchestrates parsing"""
    
    def __init__(self):
        self.parsers = {
            'pdf': PDFParser(),
            'docx': DOCXParser(),
            'txt': TextParser(),
        }
    
    def process(self, file_path: str, file_type: str) -> str:
        """
        Process document and return cleaned text
        
        Args:
            file_path: Path to the document
            file_type: Type of document (pdf, docx, txt)
        
        Returns:
            Cleaned text content
        """
        file_type = file_type.lower().replace('.', '')
        
        if file_type not in self.parsers:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        # Parse document
        parser = self.parsers[file_type]
        raw_text = parser.parse(file_path)
        
        # Clean text
        cleaned_text = self._clean_text(raw_text)
        
        return cleaned_text
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text
        
        Args:
            text: Raw text
        
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if line]
        
        # Join lines
        text = '\n'.join(lines)
        
        # Remove excessive newlines
        while '\n\n\n' in text:
            text = text.replace('\n\n\n', '\n\n')
        
        # Remove special characters that might cause issues
        text = text.replace('\x00', '')
        text = text.replace('\r', '')
        
        return text.strip()
    
    def validate_file(self, file_path: str, max_size_mb: int = 10) -> bool:
        """
        Validate file before processing
        
        Args:
            file_path: Path to file
            max_size_mb: Maximum file size in MB
        
        Returns:
            True if valid, raises ValueError otherwise
        """
        if not os.path.exists(file_path):
            raise ValueError("File does not exist")
        
        file_size = os.path.getsize(file_path)
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if file_size > max_size_bytes:
            raise ValueError(f"File size ({file_size} bytes) exceeds maximum ({max_size_bytes} bytes)")
        
        if file_size == 0:
            raise ValueError("File is empty")
        
        return True
