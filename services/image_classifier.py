"""
Image Classifier - Protects tables and important images
Critical: Never delete images with tables or 3+ lines of text
"""

import logging
from typing import List, Dict, Tuple
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import io
import numpy as np

logger = logging.getLogger(__name__)


class ImageClassifier:
    """Classifies images as decorative or important (tables/content)"""
    
    def __init__(self, config: dict):
        self.config = config
        self.area_threshold = config.get('images', {}).get('area_threshold', 0.05)
        self.min_lines_for_table = config.get('images', {}).get('min_lines_for_table', 3)
        self.keep_tables = config.get('images', {}).get('keep_tables', True)
        self.remove_decorative = config.get('images', {}).get('remove_decorative', True)
    
    def analyze_images(self, pdf_path: str) -> Dict:
        """
        Analyze all images in PDF and classify them
        
        Returns:
            dict: {
                'total_images': int,
                'decorative_images': List of image info to remove,
                'important_images': List of image info to keep,
                'table_images': List of detected tables,
                'preview': Sample classifications for review
            }
        """
        logger.info(f"Analyzing images in {pdf_path}")
        
        doc = fitz.open(pdf_path)
        
        total_images = 0
        decorative_images = []
        important_images = []
        table_images = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_area = page.rect.width * page.rect.height
            
            # Get all images on the page
            image_list = page.get_images(full=True)
            
            for img_index, img_info in enumerate(image_list):
                total_images += 1
                xref = img_info[0]
                
                try:
                    # Get image bbox
                    img_rects = page.get_image_rects(xref)
                    
                    if not img_rects:
                        continue
                    
                    # Use first occurrence of image on page
                    img_rect = img_rects[0]
                    img_area = img_rect.width * img_rect.height
                    area_percentage = img_area / page_area
                    
                    # Extract image for OCR analysis
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    # Perform OCR on image
                    ocr_result = self._ocr_image(image_bytes)
                    
                    # Classify image
                    classification = self._classify_image(
                        area_percentage,
                        ocr_result,
                        img_rect
                    )
                    
                    image_info = {
                        'page': page_num,
                        'xref': xref,
                        'rect': img_rect,
                        'area_percentage': area_percentage,
                        'ocr_lines': ocr_result['line_count'],
                        'ocr_confidence': ocr_result['confidence'],
                        'classification': classification,
                        'ocr_text_sample': ocr_result['text'][:100] if ocr_result['text'] else ''
                    }
                    
                    if classification == 'table':
                        table_images.append(image_info)
                        important_images.append(image_info)
                    elif classification == 'important':
                        important_images.append(image_info)
                    elif classification == 'decorative':
                        decorative_images.append(image_info)
                    
                except Exception as e:
                    logger.warning(f"Error analyzing image {xref} on page {page_num}: {e}")
                    # When in doubt, keep the image
                    important_images.append({
                        'page': page_num,
                        'xref': xref,
                        'classification': 'important',
                        'reason': 'Error during analysis - kept for safety'
                    })
        
        doc.close()
        
        logger.info(f"Image analysis complete: {total_images} total, "
                   f"{len(table_images)} tables, {len(important_images)} important, "
                   f"{len(decorative_images)} decorative")
        
        return {
            'total_images': total_images,
            'decorative_images': decorative_images,
            'important_images': important_images,
            'table_images': table_images,
            'preview': {
                'sample_decorative': decorative_images[:3],
                'sample_tables': table_images[:3],
                'sample_important': important_images[:3]
            }
        }
    
    def _ocr_image(self, image_bytes: bytes) -> Dict:
        """
        Perform OCR on image to detect text/tables
        
        Returns:
            dict: {
                'text': str,
                'line_count': int,
                'confidence': float,
                'has_table_structure': bool
            }
        """
        try:
            # Convert to PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to grayscale for better OCR
            if image.mode != 'L':
                image = image.convert('L')
            
            # Perform OCR with data
            ocr_data = pytesseract.image_to_data(
                image,
                output_type=pytesseract.Output.DICT,
                config='--psm 6'  # Assume uniform block of text
            )
            
            # Extract text
            text = pytesseract.image_to_string(image)
            
            # Count lines (non-empty text blocks)
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            line_count = len(lines)
            
            # Calculate average confidence
            confidences = [conf for conf in ocr_data['conf'] if conf != -1]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Check for table structure (aligned columns, multiple rows)
            has_table_structure = self._detect_table_structure(ocr_data)
            
            return {
                'text': text.strip(),
                'line_count': line_count,
                'confidence': avg_confidence / 100.0,  # Normalize to 0-1
                'has_table_structure': has_table_structure
            }
            
        except Exception as e:
            logger.warning(f"OCR failed on image: {e}")
            return {
                'text': '',
                'line_count': 0,
                'confidence': 0.0,
                'has_table_structure': False
            }
    
    def _detect_table_structure(self, ocr_data: Dict) -> bool:
        """
        Detect if OCR data suggests a table structure
        Looks for aligned columns and multiple rows
        """
        try:
            # Get word positions
            n_boxes = len(ocr_data['text'])
            
            if n_boxes < 6:  # Tables need at least a few cells
                return False
            
            # Group words by similar y-coordinates (rows)
            VERTICAL_TOLERANCE = 10
            rows = {}
            
            for i in range(n_boxes):
                if not ocr_data['text'][i].strip():
                    continue
                
                y = ocr_data['top'][i]
                row_key = round(y / VERTICAL_TOLERANCE) * VERTICAL_TOLERANCE
                
                if row_key not in rows:
                    rows[row_key] = []
                
                rows[row_key].append({
                    'text': ocr_data['text'][i],
                    'x': ocr_data['left'][i]
                })
            
            # Check if we have multiple rows with similar column structure
            if len(rows) < 2:
                return False
            
            # Check for column alignment across rows
            for row_data in rows.values():
                if len(row_data) >= 2:  # At least 2 columns
                    return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Error detecting table structure: {e}")
            return False
    
    def _classify_image(self, area_percentage: float, ocr_result: Dict, rect) -> str:
        """
        Classify image as 'table', 'important', or 'decorative'
        
        CRITICAL: Never classify tables or images with 3+ lines as decorative
        """
        
        # RULE 1: If has table structure, always keep
        if ocr_result['has_table_structure']:
            logger.debug("Classified as table (table structure detected)")
            return 'table'
        
        # RULE 2: If has 3+ lines of text, always keep (likely table or important content)
        if ocr_result['line_count'] >= self.min_lines_for_table:
            logger.debug(f"Classified as table ({ocr_result['line_count']} lines detected)")
            return 'table'
        
        # RULE 3: If has any meaningful text (1-2 lines), keep as important
        if ocr_result['line_count'] > 0 and len(ocr_result['text']) > 10:
            logger.debug("Classified as important (contains text)")
            return 'important'
        
        # RULE 4: Large images are likely important
        if area_percentage > 0.20:  # More than 20% of page
            logger.debug(f"Classified as important (large area: {area_percentage:.1%})")
            return 'important'
        
        # RULE 5: Medium-sized images with no text might be important
        if area_percentage > 0.10:
            logger.debug(f"Classified as important (medium area: {area_percentage:.1%})")
            return 'important'
        
        # RULE 6: Small images with no text are likely decorative
        if area_percentage < self.area_threshold and ocr_result['line_count'] == 0:
            logger.debug(f"Classified as decorative (small area: {area_percentage:.1%}, no text)")
            return 'decorative'
        
        # Default: keep image if uncertain
        logger.debug("Classified as important (default - when in doubt, keep)")
        return 'important'
    
    def remove_decorative_images(self, pdf_path: str, output_path: str,
                                  decorative_images: List[Dict]) -> int:
        """
        Remove decorative images from PDF
        
        Returns:
            int: Number of images removed
        """
        logger.info(f"Removing {len(decorative_images)} decorative images")
        
        if not self.remove_decorative:
            logger.info("Image removal disabled in config")
            return 0
        
        doc = fitz.open(pdf_path)
        removed_count = 0
        
        # Group by page for efficiency
        images_by_page = {}
        for img_info in decorative_images:
            page_num = img_info['page']
            if page_num not in images_by_page:
                images_by_page[page_num] = []
            images_by_page[page_num].append(img_info)
        
        # Remove images page by page
        for page_num, images in images_by_page.items():
            page = doc[page_num]
            
            for img_info in images:
                try:
                    # Cover image with white rectangle
                    rect = img_info['rect']
                    page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
                    removed_count += 1
                except Exception as e:
                    logger.warning(f"Error removing image on page {page_num}: {e}")
        
        doc.save(output_path, garbage=4, deflate=True)
        doc.close()
        
        logger.info(f"Removed {removed_count} decorative images")
        return removed_count
