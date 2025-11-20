"""
Preview Generator - Shows before/after comparisons
Mandatory preview before any final deletions
"""

import logging
from typing import Dict, List
import fitz  # PyMuPDF
from PIL import Image
import io
import json

logger = logging.getLogger(__name__)


class PreviewGenerator:
    """Generates preview comparisons for user review"""
    
    def __init__(self, config: dict):
        self.config = config
        self.sample_pages = config.get('preview', {}).get('sample_pages', 4)
        self.generate_comparisons = config.get('preview', {}).get('generate_comparisons', True)
    
    def generate_preview_report(self, 
                                original_pdf: str,
                                processed_pdf: str,
                                detection_results: Dict,
                                output_dir: str) -> Dict:
        """
        Generate comprehensive preview report
        
        Args:
            original_pdf: Path to original PDF
            processed_pdf: Path to processed PDF (if exists)
            detection_results: Results from header/footer and image detection
            output_dir: Directory to save preview files
        
        Returns:
            dict: Preview report with samples and statistics
        """
        logger.info("Generating preview report")
        
        preview_report = {
            'header_footer_detection': self._format_header_footer_preview(detection_results.get('headers_footers', {})),
            'image_analysis': self._format_image_preview(detection_results.get('images', {})),
            'sample_pages': [],
            'recommendations': []
        }
        
        # Generate sample page comparisons
        if self.generate_comparisons:
            preview_report['sample_pages'] = self._generate_page_comparisons(
                original_pdf,
                processed_pdf if processed_pdf else original_pdf,
                output_dir
            )
        
        # Generate recommendations
        preview_report['recommendations'] = self._generate_recommendations(detection_results)
        
        return preview_report
    
    def _format_header_footer_preview(self, hf_results: Dict) -> Dict:
        """Format header/footer detection results for preview"""
        
        if not hf_results:
            return {'status': 'not_detected'}
        
        return {
            'algorithm_used': hf_results.get('algorithm_used', 'unknown'),
            'consistency_score': round(hf_results.get('consistency_score', 0), 3),
            'headers_detected': hf_results.get('headers', []),
            'footers_detected': hf_results.get('footers', []),
            'preview_samples': hf_results.get('preview', {}),
            'count': {
                'headers': len(hf_results.get('headers', [])),
                'footers': len(hf_results.get('footers', []))
            }
        }
    
    def _format_image_preview(self, image_results: Dict) -> Dict:
        """Format image analysis results for preview"""
        
        if not image_results:
            return {'status': 'not_analyzed'}
        
        return {
            'total_images': image_results.get('total_images', 0),
            'classification_summary': {
                'decorative': len(image_results.get('decorative_images', [])),
                'tables': len(image_results.get('table_images', [])),
                'important': len(image_results.get('important_images', []))
            },
            'images_to_remove': len(image_results.get('decorative_images', [])),
            'images_to_keep': len(image_results.get('important_images', [])) + len(image_results.get('table_images', [])),
            'sample_decorative': [
                {
                    'page': img['page'],
                    'area_percentage': round(img['area_percentage'] * 100, 2),
                    'ocr_lines': img['ocr_lines']
                }
                for img in image_results.get('decorative_images', [])[:5]
            ],
            'sample_tables': [
                {
                    'page': img['page'],
                    'area_percentage': round(img['area_percentage'] * 100, 2),
                    'ocr_lines': img['ocr_lines'],
                    'text_sample': img.get('ocr_text_sample', '')
                }
                for img in image_results.get('table_images', [])[:5]
            ]
        }
    
    def _generate_page_comparisons(self, original_pdf: str, processed_pdf: str, output_dir: str) -> List[Dict]:
        """Generate before/after page comparisons"""
        
        try:
            doc_original = fitz.open(original_pdf)
            doc_processed = fitz.open(processed_pdf) if processed_pdf != original_pdf else doc_original
            
            total_pages = len(doc_original)
            
            # Select pages to sample (spread across document)
            if total_pages <= self.sample_pages:
                pages_to_sample = list(range(total_pages))
            else:
                step = total_pages // self.sample_pages
                pages_to_sample = [i * step for i in range(self.sample_pages)]
            
            comparisons = []
            
            for page_num in pages_to_sample:
                comparison = {
                    'page_number': page_num + 1,
                    'original_text_sample': '',
                    'processed_text_sample': ''
                }
                
                # Extract text samples
                if page_num < len(doc_original):
                    original_text = doc_original[page_num].get_text("text")
                    comparison['original_text_sample'] = original_text[:500]
                
                if page_num < len(doc_processed):
                    processed_text = doc_processed[page_num].get_text("text")
                    comparison['processed_text_sample'] = processed_text[:500]
                
                # Calculate text change
                original_len = len(comparison['original_text_sample'])
                processed_len = len(comparison['processed_text_sample'])
                
                if original_len > 0:
                    change_percentage = ((original_len - processed_len) / original_len) * 100
                    comparison['text_change_percentage'] = round(change_percentage, 2)
                
                comparisons.append(comparison)
            
            doc_original.close()
            if doc_processed != doc_original:
                doc_processed.close()
            
            return comparisons
            
        except Exception as e:
            logger.error(f"Error generating page comparisons: {e}")
            return []
    
    def _generate_recommendations(self, detection_results: Dict) -> List[str]:
        """Generate recommendations based on detection results"""
        
        recommendations = []
        
        # Header/Footer recommendations
        hf_results = detection_results.get('headers_footers', {})
        if hf_results:
            score = hf_results.get('consistency_score', 0)
            if score < 0.70:
                recommendations.append(
                    f"⚠️  Header/footer detection confidence is low ({score:.2f}). "
                    "Review samples carefully before proceeding."
                )
            elif score >= 0.90:
                recommendations.append(
                    f"✓ Header/footer detection confidence is high ({score:.2f}). "
                    "Safe to proceed."
                )
        
        # Image recommendations
        img_results = detection_results.get('images', {})
        if img_results:
            table_count = len(img_results.get('table_images', []))
            decorative_count = len(img_results.get('decorative_images', []))
            
            if table_count > 0:
                recommendations.append(
                    f"✓ Protected {table_count} table(s) from deletion."
                )
            
            if decorative_count > 0:
                recommendations.append(
                    f"📌 {decorative_count} decorative image(s) will be removed. "
                    "Review samples to confirm."
                )
            
            if decorative_count == 0 and img_results.get('total_images', 0) > 0:
                recommendations.append(
                    "✓ All images contain important content. Nothing will be removed."
                )
        
        if not recommendations:
            recommendations.append("No significant changes detected.")
        
        return recommendations
    
    def save_preview_report(self, report: Dict, output_path: str):
        """Save preview report to JSON file"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Preview report saved to {output_path}")
    
    def print_preview_summary(self, report: Dict):
        """Print preview summary to console"""
        
        print("\n" + "="*60)
        print("PREVIEW REPORT - REVIEW BEFORE PROCEEDING")
        print("="*60)
        
        # Header/Footer section
        hf = report.get('header_footer_detection', {})
        if hf.get('status') != 'not_detected':
            print("\n📋 HEADER/FOOTER DETECTION:")
            print(f"   Algorithm: {hf.get('algorithm_used', 'N/A')}")
            print(f"   Confidence: {hf.get('consistency_score', 0):.2%}")
            print(f"   Headers found: {hf.get('count', {}).get('headers', 0)}")
            print(f"   Footers found: {hf.get('count', {}).get('footers', 0)}")
            
            if hf.get('headers_detected'):
                print("\n   Headers to remove:")
                for h in hf['headers_detected'][:3]:
                    print(f"      - {h}")
            
            if hf.get('footers_detected'):
                print("\n   Footers to remove:")
                for f in hf['footers_detected'][:3]:
                    print(f"      - {f}")
        
        # Image section
        img = report.get('image_analysis', {})
        if img.get('status') != 'not_analyzed':
            print("\n🖼️  IMAGE ANALYSIS:")
            print(f"   Total images: {img.get('total_images', 0)}")
            summary = img.get('classification_summary', {})
            print(f"   Tables (protected): {summary.get('tables', 0)}")
            print(f"   Important: {summary.get('important', 0)}")
            print(f"   Decorative (to remove): {summary.get('decorative', 0)}")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        for rec in report.get('recommendations', []):
            print(f"   {rec}")
        
        # Sample pages
        samples = report.get('sample_pages', [])
        if samples:
            print(f"\n📄 SAMPLE PAGE COMPARISONS ({len(samples)} pages):")
            for sample in samples[:3]:
                print(f"\n   Page {sample['page_number']}:")
                if 'text_change_percentage' in sample:
                    print(f"      Text change: {sample['text_change_percentage']:.1f}%")
        
        print("\n" + "="*60)
        print("Review the above summary and the detailed JSON report.")
        print("="*60 + "\n")
