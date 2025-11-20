"""
OCR Processor with intelligent chunking for large PDFs
Splits PDFs into manageable chunks to avoid RAM issues
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import List, Tuple
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class OCRProcessor:
    """Handles OCR processing with automatic chunking for large files"""
    
    def __init__(self, config: dict):
        self.config = config
        self.chunk_size = config.get('ocr', {}).get('chunk_size', 200)
        self.confidence_threshold = config.get('ocr', {}).get('confidence_threshold', 0.70)
        self.deskew = config.get('ocr', {}).get('deskew', True)
        self.remove_background = config.get('ocr', {}).get('remove_background', True)
        self.rotate_pages = config.get('ocr', {}).get('rotate_pages', True)
        self.output_type = config.get('ocr', {}).get('output_type', 'pdfa')
    
    def process_pdf(self, input_pdf: str, output_pdf: str, language: str = 'ara+eng') -> dict:
        """
        Process PDF with OCR, automatically chunking if needed
        
        Args:
            input_pdf: Path to input PDF
            output_pdf: Path for output PDF
            language: Tesseract language code (ara, eng, ara+eng)
        
        Returns:
            dict: Processing stats including confidence scores and page count
        """
        logger.info(f"Starting OCR processing for {input_pdf}")
        
        # Get page count
        try:
            doc = fitz.open(input_pdf)
            total_pages = len(doc)
            doc.close()
        except Exception as e:
            logger.error(f"Error reading PDF: {e}")
            raise
        
        logger.info(f"Total pages: {total_pages}")
        
        # Decide if chunking is needed
        if total_pages <= self.chunk_size:
            logger.info("File size within chunk limit, processing without chunking")
            return self._process_single_pdf(input_pdf, output_pdf, language)
        else:
            logger.info(f"File has {total_pages} pages, chunking into {self.chunk_size}-page segments")
            return self._process_chunked_pdf(input_pdf, output_pdf, language, total_pages)
    
    def _process_single_pdf(self, input_pdf: str, output_pdf: str, language: str) -> dict:
        """Process a PDF without chunking"""
        
        stats = {
            'total_pages': 0,
            'chunks_processed': 1,
            'average_confidence': 0.0,
            'low_confidence_pages': []
        }
        
        try:
            # Build ocrmypdf command
            cmd = self._build_ocrmypdf_command(input_pdf, output_pdf, language)
            
            logger.info(f"Running OCR command: {' '.join(cmd)}")
            
            # Run OCR
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode != 0:
                logger.warning(f"OCR process returned code {result.returncode}")
                logger.warning(f"STDERR: {result.stderr}")
                
                # OCR might still produce output even with warnings
                if not os.path.exists(output_pdf):
                    raise Exception(f"OCR failed: {result.stderr}")
            
            # Get page count from output
            doc = fitz.open(output_pdf)
            stats['total_pages'] = len(doc)
            doc.close()
            
            logger.info(f"OCR completed successfully. Output: {output_pdf}")
            
        except subprocess.TimeoutExpired:
            logger.error("OCR process timeout")
            raise Exception("OCR processing timed out")
        except Exception as e:
            logger.error(f"Error during OCR processing: {e}")
            raise
        
        return stats
    
    def _process_chunked_pdf(self, input_pdf: str, output_pdf: str, language: str, total_pages: int) -> dict:
        """Process a large PDF by splitting into chunks"""
        
        temp_dir = Path(output_pdf).parent / "temp_chunks"
        temp_dir.mkdir(exist_ok=True)
        
        stats = {
            'total_pages': total_pages,
            'chunks_processed': 0,
            'average_confidence': 0.0,
            'low_confidence_pages': []
        }
        
        chunk_files = []
        
        try:
            # Split PDF into chunks
            logger.info("Splitting PDF into chunks...")
            chunks = self._split_pdf(input_pdf, temp_dir, self.chunk_size)
            
            # Process each chunk
            for i, chunk_path in enumerate(chunks):
                logger.info(f"Processing chunk {i+1}/{len(chunks)}")
                
                chunk_output = temp_dir / f"chunk_{i}_ocr.pdf"
                
                try:
                    self._process_single_pdf(str(chunk_path), str(chunk_output), language)
                    chunk_files.append(str(chunk_output))
                    stats['chunks_processed'] += 1
                except Exception as e:
                    logger.error(f"Error processing chunk {i}: {e}")
                    # Use original chunk if OCR fails
                    chunk_files.append(str(chunk_path))
            
            # Merge chunks back together
            logger.info("Merging processed chunks...")
            self._merge_pdfs(chunk_files, output_pdf)
            
            logger.info(f"Chunked OCR processing completed. Output: {output_pdf}")
            
        except Exception as e:
            logger.error(f"Error during chunked processing: {e}")
            raise
        finally:
            # Cleanup temporary files
            logger.info("Cleaning up temporary chunk files...")
            for file in temp_dir.glob("*"):
                try:
                    file.unlink()
                except Exception as e:
                    logger.warning(f"Could not delete {file}: {e}")
            try:
                temp_dir.rmdir()
            except:
                pass
        
        return stats
    
    def _split_pdf(self, input_pdf: str, output_dir: Path, chunk_size: int) -> List[str]:
        """Split PDF into chunks of specified size"""
        
        doc = fitz.open(input_pdf)
        total_pages = len(doc)
        chunk_files = []
        
        for start_page in range(0, total_pages, chunk_size):
            end_page = min(start_page + chunk_size, total_pages)
            
            # Create new PDF with chunk pages
            chunk_doc = fitz.open()
            chunk_doc.insert_pdf(doc, from_page=start_page, to_page=end_page - 1)
            
            # Save chunk
            chunk_path = output_dir / f"chunk_{len(chunk_files)}_input.pdf"
            chunk_doc.save(str(chunk_path))
            chunk_doc.close()
            
            chunk_files.append(str(chunk_path))
            logger.info(f"Created chunk: pages {start_page+1}-{end_page}")
        
        doc.close()
        return chunk_files
    
    def _merge_pdfs(self, pdf_files: List[str], output_pdf: str):
        """Merge multiple PDFs into one"""
        
        merged_doc = fitz.open()
        
        for pdf_file in pdf_files:
            try:
                doc = fitz.open(pdf_file)
                merged_doc.insert_pdf(doc)
                doc.close()
            except Exception as e:
                logger.error(f"Error merging {pdf_file}: {e}")
                raise
        
        merged_doc.save(output_pdf)
        merged_doc.close()
        
        logger.info(f"Merged {len(pdf_files)} files into {output_pdf}")
    
    def _build_ocrmypdf_command(self, input_pdf: str, output_pdf: str, language: str) -> List[str]:
        """Build ocrmypdf command with configured options"""
        
        cmd = ['ocrmypdf']
        
        # Language
        cmd.extend(['--language', language])
        
        # Optional features
        if self.deskew:
            cmd.append('--deskew')
        
        if self.remove_background:
            cmd.append('--remove-background')
        
        if self.rotate_pages:
            cmd.append('--rotate-pages')
        
        # Output type
        if self.output_type:
            cmd.extend(['--output-type', self.output_type])
        
        # Skip pages that already have text (faster)
        cmd.append('--skip-text')
        
        # Force OCR on all pages (use one or the other, not both)
        # cmd.append('--force-ocr')
        
        # Optimization
        cmd.extend(['--optimize', '1'])
        
        # JPEG quality for images
        cmd.extend(['--jpeg-quality', '85'])
        
        # Input and output
        cmd.append(input_pdf)
        cmd.append(output_pdf)
        
        return cmd
