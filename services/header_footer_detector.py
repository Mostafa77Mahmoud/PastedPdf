"""
Header/Footer Detection with Multiple Algorithms
Uses 3 different approaches and selects the best based on consistency score
"""

import logging
import re
from typing import List, Dict, Tuple, Set
from collections import Counter
import fitz  # PyMuPDF
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class HeaderFooterDetector:
    """Detects repeated headers and footers using multiple algorithms"""
    
    def __init__(self, config: dict):
        self.config = config
        self.threshold = config.get('header_footer', {}).get('detection_threshold', 0.85)
        self.sample_pages = config.get('header_footer', {}).get('sample_pages', 50)
        self.use_multi_algorithm = config.get('header_footer', {}).get('use_multi_algorithm', True)
        self.algorithms = config.get('header_footer', {}).get('algorithms', [
            'text_repetition',
            'bbox_matching',
            'fuzzy_matching'
        ])
    
    def detect(self, pdf_path: str) -> Dict:
        """
        Detect headers and footers using configured algorithms
        
        Returns:
            dict: {
                'headers': List of header text patterns to remove,
                'footers': List of footer text patterns to remove,
                'algorithm_used': Name of algorithm with best consistency,
                'consistency_score': Score of selected algorithm,
                'preview': Sample detections for user review
            }
        """
        logger.info(f"Starting header/footer detection for {pdf_path}")
        
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        # Determine pages to sample
        pages_to_check = min(self.sample_pages, total_pages)
        start_pages = list(range(min(pages_to_check, total_pages)))
        end_pages = list(range(max(0, total_pages - pages_to_check), total_pages))
        sample_pages = sorted(set(start_pages + end_pages))
        
        logger.info(f"Sampling {len(sample_pages)} pages from total {total_pages}")
        
        results = {}
        
        # Run all configured algorithms
        if 'text_repetition' in self.algorithms:
            results['text_repetition'] = self._algorithm_text_repetition(doc, sample_pages)
        
        if 'bbox_matching' in self.algorithms:
            results['bbox_matching'] = self._algorithm_bbox_matching(doc, sample_pages)
        
        if 'fuzzy_matching' in self.algorithms:
            results['fuzzy_matching'] = self._algorithm_fuzzy_matching(doc, sample_pages)
        
        doc.close()
        
        # Select best algorithm based on consistency score
        best_algorithm = max(results.items(), key=lambda x: x[1]['consistency_score'])
        
        logger.info(f"Best algorithm: {best_algorithm[0]} with score {best_algorithm[1]['consistency_score']:.2f}")
        
        result = best_algorithm[1]
        result['algorithm_used'] = best_algorithm[0]
        
        return result
    
    def _algorithm_text_repetition(self, doc, sample_pages: List[int]) -> Dict:
        """
        Algorithm 1: Simple text repetition analysis
        Looks for exact text matches in top/bottom of pages
        """
        logger.info("Running algorithm: text_repetition")
        
        header_candidates = Counter()
        footer_candidates = Counter()
        total_sampled = len(sample_pages)
        
        for page_num in sample_pages:
            page = doc[page_num]
            blocks = page.get_text("blocks")
            
            if not blocks:
                continue
            
            # Sort blocks by vertical position
            blocks = sorted(blocks, key=lambda b: b[1])  # b[1] is y0
            
            # Top 2 blocks as potential headers
            for block in blocks[:2]:
                text = block[4].strip()
                if text and len(text) > 3:  # Ignore very short text
                    header_candidates[text] += 1
            
            # Bottom 2 blocks as potential footers
            for block in blocks[-2:]:
                text = block[4].strip()
                if text and len(text) > 3:
                    footer_candidates[text] += 1
        
        # Filter by threshold
        headers = [text for text, count in header_candidates.items() 
                   if count / total_sampled >= self.threshold]
        footers = [text for text, count in footer_candidates.items() 
                   if count / total_sampled >= self.threshold]
        
        # Calculate consistency score
        consistency_score = 0
        if header_candidates:
            consistency_score += max(header_candidates.values()) / total_sampled
        if footer_candidates:
            consistency_score += max(footer_candidates.values()) / total_sampled
        consistency_score = consistency_score / 2 if (header_candidates or footer_candidates) else 0
        
        return {
            'headers': headers,
            'footers': footers,
            'consistency_score': consistency_score,
            'preview': {
                'header_samples': list(header_candidates.most_common(3)),
                'footer_samples': list(footer_candidates.most_common(3))
            }
        }
    
    def _algorithm_bbox_matching(self, doc, sample_pages: List[int]) -> Dict:
        """
        Algorithm 2: Bounding box position matching
        Looks for text blocks in similar positions across pages
        """
        logger.info("Running algorithm: bbox_matching")
        
        # Tolerance for position matching (in points)
        POSITION_TOLERANCE = 10
        
        header_positions = {}  # {(x0, y0): [texts]}
        footer_positions = {}
        
        for page_num in sample_pages:
            page = doc[page_num]
            blocks = page.get_text("blocks")
            
            if not blocks:
                continue
            
            page_height = page.rect.height
            
            for block in blocks:
                x0, y0, x1, y1, text = block[0], block[1], block[2], block[3], block[4].strip()
                
                if not text or len(text) < 3:
                    continue
                
                # Normalize position
                pos_key = (round(x0 / POSITION_TOLERANCE) * POSITION_TOLERANCE,
                          round(y0 / POSITION_TOLERANCE) * POSITION_TOLERANCE)
                
                # Check if in header region (top 10%)
                if y0 < page_height * 0.10:
                    if pos_key not in header_positions:
                        header_positions[pos_key] = []
                    header_positions[pos_key].append(text)
                
                # Check if in footer region (bottom 10%)
                elif y0 > page_height * 0.90:
                    if pos_key not in footer_positions:
                        footer_positions[pos_key] = []
                    footer_positions[pos_key].append(text)
        
        # Find positions with repeated text
        total_sampled = len(sample_pages)
        headers = []
        footers = []
        
        for pos, texts in header_positions.items():
            # Most common text at this position
            text_counter = Counter(texts)
            most_common_text, count = text_counter.most_common(1)[0]
            if count / total_sampled >= self.threshold:
                headers.append(most_common_text)
        
        for pos, texts in footer_positions.items():
            text_counter = Counter(texts)
            most_common_text, count = text_counter.most_common(1)[0]
            if count / total_sampled >= self.threshold:
                footers.append(most_common_text)
        
        # Calculate consistency score
        consistency_score = 0
        if header_positions:
            max_header_match = max(len(texts) for texts in header_positions.values())
            consistency_score += max_header_match / total_sampled
        if footer_positions:
            max_footer_match = max(len(texts) for texts in footer_positions.values())
            consistency_score += max_footer_match / total_sampled
        consistency_score = consistency_score / 2 if (header_positions or footer_positions) else 0
        
        return {
            'headers': list(set(headers)),
            'footers': list(set(footers)),
            'consistency_score': consistency_score,
            'preview': {
                'header_positions_found': len(header_positions),
                'footer_positions_found': len(footer_positions)
            }
        }
    
    def _algorithm_fuzzy_matching(self, doc, sample_pages: List[int]) -> Dict:
        """
        Algorithm 3: Fuzzy string matching
        Handles variations in headers/footers (e.g., page numbers)
        """
        logger.info("Running algorithm: fuzzy_matching")
        
        SIMILARITY_THRESHOLD = 0.85
        
        header_groups = []
        footer_groups = []
        
        for page_num in sample_pages:
            page = doc[page_num]
            blocks = page.get_text("blocks")
            
            if not blocks:
                continue
            
            blocks = sorted(blocks, key=lambda b: b[1])
            page_height = page.rect.height
            
            # Extract potential headers and footers
            for block in blocks:
                y0 = block[1]
                text = block[4].strip()
                
                if not text or len(text) < 3:
                    continue
                
                # Remove numbers (likely page numbers) for comparison
                text_normalized = re.sub(r'\d+', '#', text)
                
                if y0 < page_height * 0.10:
                    # Header
                    self._add_to_fuzzy_group(header_groups, text_normalized, text, SIMILARITY_THRESHOLD)
                elif y0 > page_height * 0.90:
                    # Footer
                    self._add_to_fuzzy_group(footer_groups, text_normalized, text, SIMILARITY_THRESHOLD)
        
        # Select groups that appear frequently
        total_sampled = len(sample_pages)
        headers = []
        footers = []
        
        for group in header_groups:
            if len(group['examples']) / total_sampled >= self.threshold:
                # Use the normalized pattern with wildcard
                headers.append(group['pattern'])
        
        for group in footer_groups:
            if len(group['examples']) / total_sampled >= self.threshold:
                footers.append(group['pattern'])
        
        # Calculate consistency score
        consistency_score = 0
        if header_groups:
            max_header_size = max(len(g['examples']) for g in header_groups)
            consistency_score += max_header_size / total_sampled
        if footer_groups:
            max_footer_size = max(len(g['examples']) for g in footer_groups)
            consistency_score += max_footer_size / total_sampled
        consistency_score = consistency_score / 2 if (header_groups or footer_groups) else 0
        
        return {
            'headers': headers,
            'footers': footers,
            'consistency_score': consistency_score,
            'preview': {
                'header_groups': len(header_groups),
                'footer_groups': len(footer_groups)
            }
        }
    
    def _add_to_fuzzy_group(self, groups: List[Dict], pattern: str, example: str, threshold: float):
        """Add text to a fuzzy matching group"""
        
        # Try to find existing similar group
        for group in groups:
            similarity = SequenceMatcher(None, group['pattern'], pattern).ratio()
            if similarity >= threshold:
                group['examples'].append(example)
                return
        
        # Create new group
        groups.append({
            'pattern': pattern,
            'examples': [example]
        })
    
    def remove_headers_footers(self, pdf_path: str, output_path: str, 
                               headers: List[str], footers: List[str]) -> int:
        """
        Remove detected headers and footers from PDF
        
        Returns:
            int: Number of text blocks removed
        """
        logger.info(f"Removing headers/footers from {pdf_path}")
        
        doc = fitz.open(pdf_path)
        removed_count = 0
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict")["blocks"]
            
            for block in blocks:
                if "lines" not in block:
                    continue
                
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        
                        # Check if text matches any header/footer pattern
                        should_remove = False
                        
                        for header in headers:
                            if self._text_matches_pattern(text, header):
                                should_remove = True
                                break
                        
                        if not should_remove:
                            for footer in footers:
                                if self._text_matches_pattern(text, footer):
                                    should_remove = True
                                    break
                        
                        if should_remove:
                            # Add white rectangle over the text
                            rect = fitz.Rect(span["bbox"])
                            page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
                            removed_count += 1
        
        doc.save(output_path, garbage=4, deflate=True)
        doc.close()
        
        logger.info(f"Removed {removed_count} header/footer instances")
        return removed_count
    
    def _text_matches_pattern(self, text: str, pattern: str) -> bool:
        """Check if text matches pattern (with wildcard support)"""
        
        # Exact match
        if text == pattern:
            return True
        
        # Pattern with wildcards (# represents any digit)
        pattern_regex = pattern.replace('#', r'\d+')
        if re.fullmatch(pattern_regex, text):
            return True
        
        # Fuzzy match for slight variations
        similarity = SequenceMatcher(None, text, pattern).ratio()
        if similarity >= 0.90:
            return True
        
        return False
