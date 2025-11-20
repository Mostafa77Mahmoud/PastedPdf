"""
PDF Utilities - Helper functions for PDF operations
"""

import logging
import shutil
from pathlib import Path
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class PDFUtils:
    """Utility functions for PDF operations"""
    
    @staticmethod
    def create_backup(pdf_path: str, backup_suffix: str = '_backup') -> str:
        """
        Create a backup copy of PDF
        
        Returns:
            str: Path to backup file
        """
        pdf_file = Path(pdf_path)
        backup_path = pdf_file.parent / f"{pdf_file.stem}{backup_suffix}{pdf_file.suffix}"
        
        shutil.copy2(pdf_path, backup_path)
        logger.info(f"Created backup: {backup_path}")
        
        return str(backup_path)
    
    @staticmethod
    def get_pdf_info(pdf_path: str) -> dict:
        """Get basic PDF information"""
        
        try:
            doc = fitz.open(pdf_path)
            
            info = {
                'pages': len(doc),
                'file_size_mb': Path(pdf_path).stat().st_size / (1024 * 1024),
                'metadata': doc.metadata,
                'is_encrypted': doc.is_encrypted,
                'has_text': False
            }
            
            # Check if PDF has text (quick check on first page)
            if len(doc) > 0:
                text = doc[0].get_text()
                info['has_text'] = len(text.strip()) > 0
            
            doc.close()
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting PDF info: {e}")
            return {}
    
    @staticmethod
    def save_as_copies(pdf_path: str, output_dir: str, base_name: str) -> dict:
        """
        Save PDF with three versions: raw, ocr, cleaned
        
        Returns:
            dict: Paths to the three versions
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Copy as raw version
        raw_path = output_path / f"{base_name}_raw.pdf"
        shutil.copy2(pdf_path, raw_path)
        
        return {
            'raw': str(raw_path),
            'ocr': str(output_path / f"{base_name}_ocr.pdf"),
            'cleaned': str(output_path / f"{base_name}_cleaned.pdf")
        }
    
    @staticmethod
    def validate_pdf(pdf_path: str) -> bool:
        """Validate that PDF can be opened and read"""
        
        try:
            doc = fitz.open(pdf_path)
            is_valid = len(doc) > 0
            doc.close()
            return is_valid
        except Exception as e:
            logger.error(f"PDF validation failed: {e}")
            return False
