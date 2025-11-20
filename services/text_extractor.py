"""
Text Extractor with RTL/LTR auto-detection and Unicode preservation
CRITICAL: No text modification, reshaping, or spell correction
"""

import logging
import unicodedata
from typing import Dict, List
import fitz  # PyMuPDF
import re

logger = logging.getLogger(__name__)


class TextExtractor:
    """Extracts text from PDF with proper RTL/LTR handling"""
    
    def __init__(self, config: dict):
        self.config = config
        self.preserve_unicode = config.get('text', {}).get('preserve_unicode', True)
        self.auto_detect_direction = config.get('text', {}).get('auto_detect_direction', True)
        self.normalization = config.get('text', {}).get('normalization', 'NFC')
        self.preserve_formatting = config.get('text', {}).get('preserve_formatting', True)
    
    def extract_text(self, pdf_path: str, headers: List[str] = None, 
                     footers: List[str] = None) -> Dict:
        """
        Extract text from PDF with proper handling
        
        Args:
            pdf_path: Path to PDF file
            headers: List of header patterns to remove
            footers: List of footer patterns to remove
        
        Returns:
            dict: {
                'text': Full extracted text,
                'page_texts': List of text per page,
                'total_pages': int,
                'rtl_pages': List of page numbers with RTL text,
                'ltr_pages': List of page numbers with LTR text
            }
        """
        logger.info(f"Extracting text from {pdf_path}")
        
        doc = fitz.open(pdf_path)
        
        page_texts = []
        rtl_pages = []
        ltr_pages = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Extract text with layout preservation
            if self.preserve_formatting:
                text = page.get_text("text")
            else:
                text = page.get_text("text")
            
            # Remove headers and footers
            if headers or footers:
                text = self._remove_headers_footers_from_text(text, headers, footers)
            
            # Detect text direction
            direction = self._detect_text_direction(text)
            if direction == 'RTL':
                rtl_pages.append(page_num)
            else:
                ltr_pages.append(page_num)
            
            # Normalize Unicode (NO reshaping or modification)
            if self.preserve_unicode:
                text = self._normalize_unicode(text)
            
            page_texts.append(text)
        
        doc.close()
        
        # Combine all pages
        full_text = '\n\n'.join(page_texts)
        
        logger.info(f"Extracted {len(full_text)} characters from {len(page_texts)} pages")
        logger.info(f"RTL pages: {len(rtl_pages)}, LTR pages: {len(ltr_pages)}")
        
        return {
            'text': full_text,
            'page_texts': page_texts,
            'total_pages': len(page_texts),
            'rtl_pages': rtl_pages,
            'ltr_pages': ltr_pages
        }
    
    def _detect_text_direction(self, text: str) -> str:
        """
        Auto-detect if text is RTL or LTR
        
        Returns:
            'RTL' or 'LTR'
        """
        if not self.auto_detect_direction:
            return 'LTR'
        
        # Count RTL and LTR characters
        rtl_count = 0
        ltr_count = 0
        
        for char in text:
            # Check Unicode bidirectional class
            bidi_class = unicodedata.bidirectional(char)
            
            if bidi_class in ('R', 'AL'):  # Right-to-Left, Arabic Letter
                rtl_count += 1
            elif bidi_class in ('L',):  # Left-to-Right
                ltr_count += 1
        
        # Determine dominant direction
        if rtl_count > ltr_count:
            return 'RTL'
        else:
            return 'LTR'
    
    def _normalize_unicode(self, text: str) -> str:
        """
        Normalize Unicode text (NO modification of content)
        
        Only performs canonical normalization, no reshaping
        """
        if not text:
            return text
        
        # Apply Unicode normalization
        # NFC = Canonical Decomposition, followed by Canonical Composition
        # This ensures consistent representation without changing content
        if self.normalization in ('NFC', 'NFD', 'NFKC', 'NFKD'):
            text = unicodedata.normalize(self.normalization, text)
        
        return text
    
    def _remove_headers_footers_from_text(self, text: str, 
                                          headers: List[str], 
                                          footers: List[str]) -> str:
        """
        Remove header/footer lines from extracted text
        """
        if not text:
            return text
        
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line_stripped = line.strip()
            
            # Check if line matches any header
            is_header_footer = False
            
            if headers:
                for header in headers:
                    if self._line_matches_pattern(line_stripped, header):
                        is_header_footer = True
                        break
            
            if not is_header_footer and footers:
                for footer in footers:
                    if self._line_matches_pattern(line_stripped, footer):
                        is_header_footer = True
                        break
            
            if not is_header_footer:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _line_matches_pattern(self, line: str, pattern: str) -> bool:
        """Check if line matches header/footer pattern"""
        
        # Exact match
        if line == pattern:
            return True
        
        # Pattern with wildcards
        pattern_regex = pattern.replace('#', r'\d+')
        if re.fullmatch(pattern_regex, line):
            return True
        
        # Fuzzy match
        from difflib import SequenceMatcher
        similarity = SequenceMatcher(None, line, pattern).ratio()
        if similarity >= 0.90:
            return True
        
        return False
    
    def save_text(self, text: str, output_path: str):
        """Save text to file with proper UTF-8 encoding"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        logger.info(f"Saved text to {output_path}")
    
    def generate_chunk_simulation(self, text: str, chunk_size: int = 2000) -> List[str]:
        """
        Generate chunks to simulate how text will appear in Gemini File Search
        
        This helps verify that cleaning didn't break context
        """
        chunks = []
        
        # Split into chunks while trying to preserve sentence boundaries
        words = text.split()
        current_chunk = []
        current_size = 0
        
        for word in words:
            word_size = len(word) + 1  # +1 for space
            
            if current_size + word_size > chunk_size and current_chunk:
                # Save current chunk
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_size = word_size
            else:
                current_chunk.append(word)
                current_size += word_size
        
        # Add last chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        logger.info(f"Generated {len(chunks)} chunks (avg size: {sum(len(c) for c in chunks) // len(chunks)} chars)")
        
        return chunks
