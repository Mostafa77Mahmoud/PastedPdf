"""
Enhanced Text Processor with Markdown Formatting and Quranic Noise Removal
معالج نصوص محسّن مع تنسيق Markdown وإزالة الرموز القرآنية

CRITICAL FEATURES:
1. Markdown structuring based on font size
2. Intelligent Quranic noise removal (preserves valid English terms)
3. RTL text handling with arabic-reshaper and python-bidi
"""

import logging
import re
from typing import Dict, List, Tuple
import pdfplumber
from arabic_reshaper import ArabicReshaper
from bidi.algorithm import get_display

logger = logging.getLogger(__name__)


class EnhancedTextProcessor:
    """معالج نصوص محسّن لملفات AAOIFI والمعايير الشرعية"""
    
    def __init__(self, config: dict):
        self.config = config
        
        # Markdown settings
        self.enable_markdown = config.get('text', {}).get('enable_markdown', True)
        self.font_size_threshold_h1 = config.get('text', {}).get('h1_font_size', 16)
        self.font_size_threshold_h2 = config.get('text', {}).get('h2_font_size', 14)
        
        # Quranic noise removal settings
        self.remove_quranic_noise = config.get('text', {}).get('remove_quranic_noise', True)
        self.quranic_placeholder = config.get('text', {}).get('quranic_placeholder', '[نص قرآني]')
        
        # Valid English financial terms to preserve
        self.valid_english_terms = {
            # Islamic Finance Terms
            'SUKUK', 'MURABAHA', 'MUSHARAKA', 'MUDARABA', 'IJARA', 'ISTISNA',
            'SALAM', 'TAKAFUL', 'WADIAH', 'QARD', 'WAKALAH', 'HIBAH',
            'SHARIA', 'SHARIAH', 'FIQH', 'HALAL', 'HARAM', 'RIBA',
            
            # Financial Terms
            'SWAPS', 'OPTIONS', 'DERIVATIVES', 'BONDS', 'EQUITY', 'DEBT',
            'ASSETS', 'LIABILITIES', 'CAPITAL', 'PROFIT', 'LOSS', 'REVENUE',
            'ACCOUNTING', 'FINANCIAL', 'AUDIT', 'COMPLIANCE', 'RISK',
            'INVESTMENT', 'FINANCING', 'LEASE', 'SALE', 'PURCHASE',
            
            # Organizations
            'AAOIFI', 'IFSB', 'IIFM', 'ISRA', 'CIBAFI', 'IDB', 'IRTI',
            
            # Common abbreviations
            'FAS', 'GSIFI', 'IAS', 'IFRS', 'USD', 'EUR', 'GBP', 'SAR',
            'CEO', 'CFO', 'CRO', 'GDP', 'ROA', 'ROE', 'NPV', 'IRR'
        }
        
        # Initialize Arabic reshaper
        self.reshaper = ArabicReshaper()
    
    def extract_text_with_structure(self, pdf_path: str) -> Dict:
        """
        استخراج النص مع الهيكلة (Markdown) والتنظيف الذكي
        
        Returns:
            dict: {
                'markdown_text': str,      # النص بصيغة Markdown
                'plain_text': str,         # النص العادي (بدون Markdown)
                'structure_info': dict,    # معلومات الهيكل
                'cleaning_stats': dict     # إحصائيات التنظيف
            }
        """
        logger.info(f"Extracting structured text from {pdf_path}")
        
        markdown_lines = []
        plain_lines = []
        structure_info = {
            'h1_count': 0,
            'h2_count': 0,
            'body_count': 0
        }
        cleaning_stats = {
            'quranic_sequences_removed': 0,
            'english_terms_preserved': 0
        }
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                logger.debug(f"Processing page {page_num + 1}/{len(pdf.pages)}")
                
                # Extract text with font information
                words = page.extract_words(
                    x_tolerance=3,
                    y_tolerance=3,
                    keep_blank_chars=True,
                    use_text_flow=True
                )
                
                if not words:
                    continue
                
                # Group words into lines
                lines = self._group_words_into_lines(words)
                
                # Process each line
                for line_data in lines:
                    text = line_data['text'].strip()
                    font_size = line_data['avg_font_size']
                    
                    if not text:
                        continue
                    
                    # Clean Quranic noise
                    cleaned_text, quranic_removed, english_preserved = self._clean_quranic_noise(text)
                    cleaning_stats['quranic_sequences_removed'] += quranic_removed
                    cleaning_stats['english_terms_preserved'] += english_preserved
                    
                    # Determine line type based on font size
                    if self.enable_markdown:
                        if font_size >= self.font_size_threshold_h1:
                            # Main Header
                            markdown_lines.append(f"# {cleaned_text}")
                            plain_lines.append(cleaned_text)
                            structure_info['h1_count'] += 1
                            
                        elif font_size >= self.font_size_threshold_h2:
                            # Sub Header
                            markdown_lines.append(f"## {cleaned_text}")
                            plain_lines.append(cleaned_text)
                            structure_info['h2_count'] += 1
                            
                        else:
                            # Body text
                            markdown_lines.append(cleaned_text)
                            plain_lines.append(cleaned_text)
                            structure_info['body_count'] += 1
                    else:
                        markdown_lines.append(cleaned_text)
                        plain_lines.append(cleaned_text)
                        structure_info['body_count'] += 1
        
        # Join lines
        markdown_text = '\n\n'.join(markdown_lines)
        plain_text = '\n\n'.join(plain_lines)
        
        logger.info(f"Structure: {structure_info['h1_count']} H1, {structure_info['h2_count']} H2, {structure_info['body_count']} body paragraphs")
        logger.info(f"Cleaning: Removed {cleaning_stats['quranic_sequences_removed']} Quranic sequences, preserved {cleaning_stats['english_terms_preserved']} English terms")
        
        return {
            'markdown_text': markdown_text,
            'plain_text': plain_text,
            'structure_info': structure_info,
            'cleaning_stats': cleaning_stats
        }
    
    def _group_words_into_lines(self, words: List[dict]) -> List[dict]:
        """Group words into lines based on vertical position"""
        
        if not words:
            return []
        
        # Sort words by vertical position (top to bottom)
        sorted_words = sorted(words, key=lambda w: (w['top'], w['x0']))
        
        lines = []
        current_line = []
        current_y = None
        y_tolerance = 3
        
        for word in sorted_words:
            if current_y is None:
                current_y = word['top']
                current_line = [word]
            elif abs(word['top'] - current_y) <= y_tolerance:
                # Same line
                current_line.append(word)
            else:
                # New line
                if current_line:
                    lines.append(self._process_line(current_line))
                current_line = [word]
                current_y = word['top']
        
        # Add last line
        if current_line:
            lines.append(self._process_line(current_line))
        
        return lines
    
    def _process_line(self, words: List[dict]) -> dict:
        """Process a line of words to extract text and font info"""
        
        # Sort words by horizontal position (RTL-aware)
        sorted_words = sorted(words, key=lambda w: w['x0'])
        
        # Extract text
        text = ' '.join(w['text'] for w in sorted_words)
        
        # Calculate average font size
        font_sizes = [w.get('size', 12) for w in sorted_words if 'size' in w]
        avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 12
        
        return {
            'text': text,
            'avg_font_size': avg_font_size,
            'word_count': len(sorted_words)
        }
    
    def _clean_quranic_noise(self, text: str) -> Tuple[str, int, int]:
        """
        إزالة الحروف اللاتينية العشوائية (خط القرآن المكسور) مع الحفاظ على المصطلحات الحقيقية
        
        Returns:
            (cleaned_text, quranic_sequences_removed, english_terms_preserved)
        """
        if not self.remove_quranic_noise:
            return text, 0, 0
        
        quranic_removed = 0
        english_preserved = 0
        
        # Pattern 1: Single Latin letters with spaces (e.g., "U T S R Q P")
        # This is the most common Quranic font artifact
        pattern_single_letters = r'\b[A-Z]\s+[A-Z]\s+[A-Z](?:\s+[A-Z])*\b'
        
        def replace_single_letters(match):
            nonlocal quranic_removed
            matched_text = match.group(0)
            
            # Check if it's a valid abbreviation (like "U S A" or "U A E")
            cleaned_letters = matched_text.replace(' ', '')
            if cleaned_letters in self.valid_english_terms:
                return matched_text
            
            # It's Quranic noise - replace it
            quranic_removed += 1
            return self.quranic_placeholder
        
        text = re.sub(pattern_single_letters, replace_single_letters, text)
        
        # Pattern 2: Random Latin character sequences in Arabic context
        # Look for isolated Latin words that are not in our valid terms list
        pattern_latin_words = r'\b[A-Za-z]{2,15}\b'
        
        def check_latin_word(match):
            nonlocal quranic_removed, english_preserved
            word = match.group(0).upper()
            
            # Check if it's a valid term
            if word in self.valid_english_terms:
                english_preserved += 1
                return match.group(0)  # Keep original case
            
            # Check if it looks like a real English word (has vowels)
            vowels = sum(1 for c in word if c in 'AEIOU')
            consonants = len(word) - vowels
            
            # Real English words typically have at least 1 vowel
            # and a reasonable vowel-to-consonant ratio
            if vowels >= 1 and consonants / len(word) < 0.8:
                # Looks like a real word, keep it
                return match.group(0)
            
            # Check if it's surrounded by Arabic characters
            # If yes, it's likely Quranic noise
            start_pos = match.start()
            end_pos = match.end()
            
            # Get context (10 chars before and after)
            context_before = text[max(0, start_pos-10):start_pos]
            context_after = text[end_pos:min(len(text), end_pos+10)]
            
            # Check if context contains Arabic characters
            has_arabic_before = any('\u0600' <= c <= '\u06FF' for c in context_before)
            has_arabic_after = any('\u0600' <= c <= '\u06FF' for c in context_after)
            
            if has_arabic_before or has_arabic_after:
                # Surrounded by Arabic, likely Quranic noise
                quranic_removed += 1
                return self.quranic_placeholder
            
            # Keep it
            return match.group(0)
        
        text = re.sub(pattern_latin_words, check_latin_word, text)
        
        # Pattern 3: Remove duplicate placeholders
        text = re.sub(rf'{re.escape(self.quranic_placeholder)}(\s*{re.escape(self.quranic_placeholder)})+',
                      self.quranic_placeholder, text)
        
        # Clean up extra spaces around placeholders
        text = re.sub(rf'\s+{re.escape(self.quranic_placeholder)}\s+', f' {self.quranic_placeholder} ', text)
        
        return text, quranic_removed, english_preserved
    
    def apply_rtl_formatting(self, text: str) -> str:
        """
        تطبيق التنسيق الصحيح للنصوص العربية RTL
        
        استخدام arabic-reshaper و python-bidi لضمان عرض النص بشكل صحيح
        """
        # Reshape Arabic text (connect letters properly)
        reshaped_text = self.reshaper.reshape(text)
        
        # Apply bidirectional algorithm for proper RTL display
        bidi_text = get_display(reshaped_text)
        
        return bidi_text
    
    def save_markdown_file(self, markdown_text: str, output_path: str):
        """حفظ الملف بصيغة Markdown مع UTF-8"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_text)
        
        logger.info(f"Saved Markdown file to {output_path}")
    
    def save_rtl_text_file(self, text: str, output_path: str):
        """حفظ ملف نصي مع تنسيق RTL صحيح"""
        
        # Apply RTL formatting
        rtl_text = self.apply_rtl_formatting(text)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(rtl_text)
        
        logger.info(f"Saved RTL text file to {output_path}")
