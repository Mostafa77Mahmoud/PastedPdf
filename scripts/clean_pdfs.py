#!/usr/bin/env python3
"""
PDF Cleaning Tool - Main Script
Cleans and prepares Arabic and English PDFs for Gemini File Search
"""

import os
import sys
import argparse
import logging
import time
import json
from pathlib import Path
import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.ocr_processor import OCRProcessor
from services.header_footer_detector import HeaderFooterDetector
from services.image_classifier import ImageClassifier
from services.text_extractor import TextExtractor
from services.preview_generator import PreviewGenerator
from services.pdf_utils import PDFUtils


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('pdf_cleaning.log')
        ]
    )
    
    return logging.getLogger(__name__)


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file"""
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        logging.error(f"Config file not found: {config_path}")
        logging.info("Creating default config from config.yaml.example...")
        
        # Try to copy example config
        example_path = 'config.yaml.example'
        if Path(example_path).exists():
            import shutil
            shutil.copy(example_path, config_path)
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        else:
            raise Exception("No config file found. Please create config.yaml")
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        raise


def process_pdf_file(pdf_path: str, config: dict, preview_only: bool = False) -> dict:
    """
    Process a single PDF file
    
    Args:
        pdf_path: Path to PDF file
        config: Configuration dictionary
        preview_only: If True, only generate preview without final processing
    
    Returns:
        dict: Processing report
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Processing PDF: {pdf_path}")
    
    start_time = time.time()
    
    pdf_file = Path(pdf_path)
    base_name = pdf_file.stem
    
    # Get language for this file
    language_mapping = config.get('language_per_file', {})
    language = language_mapping.get(pdf_file.name, 'ara+eng')
    
    logger.info(f"Using language: {language}")
    
    # Setup output directories
    output_dir = Path(config.get('output_dir', 'output'))
    output_dir.mkdir(parents=True, exist_ok=True)
    
    report_dir = Path(config.get('report_dir', 'report'))
    report_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize services
    ocr_processor = OCRProcessor(config)
    hf_detector = HeaderFooterDetector(config)
    img_classifier = ImageClassifier(config)
    text_extractor = TextExtractor(config)
    preview_gen = PreviewGenerator(config)
    
    # Create backup and version paths
    if config.get('safety', {}).get('create_backups', True):
        versions = PDFUtils.save_as_copies(pdf_path, str(output_dir), base_name)
        logger.info(f"Created backup: {versions['raw']}")
    else:
        versions = {
            'raw': pdf_path,
            'ocr': str(output_dir / f"{base_name}_ocr.pdf"),
            'cleaned': str(output_dir / f"{base_name}_cleaned.pdf")
        }
    
    report = {
        'file_name': pdf_file.name,
        'language': language,
        'start_time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'versions': versions,
        'steps': {}
    }
    
    # STEP 1: OCR Processing with chunking
    logger.info("STEP 1: OCR Processing")
    try:
        ocr_stats = ocr_processor.process_pdf(
            pdf_path,
            versions['ocr'],
            language
        )
        report['steps']['ocr'] = {
            'status': 'completed',
            'stats': ocr_stats
        }
        logger.info(f"OCR completed: {ocr_stats['total_pages']} pages")
    except Exception as e:
        logger.error(f"OCR processing failed: {e}")
        report['steps']['ocr'] = {
            'status': 'failed',
            'error': str(e)
        }
        # Use original file if OCR fails
        versions['ocr'] = pdf_path
    
    # STEP 2: Header/Footer Detection
    logger.info("STEP 2: Header/Footer Detection")
    try:
        hf_results = hf_detector.detect(versions['ocr'])
        report['steps']['header_footer_detection'] = {
            'status': 'completed',
            'results': {
                'algorithm_used': hf_results['algorithm_used'],
                'consistency_score': hf_results['consistency_score'],
                'headers_count': len(hf_results['headers']),
                'footers_count': len(hf_results['footers']),
                'headers': hf_results['headers'],
                'footers': hf_results['footers']
            }
        }
        logger.info(f"Detected {len(hf_results['headers'])} headers, {len(hf_results['footers'])} footers")
    except Exception as e:
        logger.error(f"Header/footer detection failed: {e}")
        hf_results = {'headers': [], 'footers': [], 'consistency_score': 0}
        report['steps']['header_footer_detection'] = {
            'status': 'failed',
            'error': str(e)
        }
    
    # STEP 3: Image Analysis
    logger.info("STEP 3: Image Analysis")
    try:
        img_results = img_classifier.analyze_images(versions['ocr'])
        report['steps']['image_analysis'] = {
            'status': 'completed',
            'results': {
                'total_images': img_results['total_images'],
                'tables_protected': len(img_results['table_images']),
                'important_kept': len(img_results['important_images']),
                'decorative_to_remove': len(img_results['decorative_images'])
            }
        }
        logger.info(f"Images: {img_results['total_images']} total, "
                   f"{len(img_results['table_images'])} tables (protected)")
    except Exception as e:
        logger.error(f"Image analysis failed: {e}")
        img_results = {'decorative_images': [], 'table_images': [], 'important_images': []}
        report['steps']['image_analysis'] = {
            'status': 'failed',
            'error': str(e)
        }
    
    # STEP 4: Generate Preview
    logger.info("STEP 4: Generating Preview")
    try:
        detection_results = {
            'headers_footers': hf_results,
            'images': img_results
        }
        
        preview_report = preview_gen.generate_preview_report(
            pdf_path,
            versions['ocr'],
            detection_results,
            str(report_dir)
        )
        
        # Save preview report
        preview_path = report_dir / f"{base_name}_preview.json"
        preview_gen.save_preview_report(preview_report, str(preview_path))
        
        # Print preview to console
        preview_gen.print_preview_summary(preview_report)
        
        report['steps']['preview'] = {
            'status': 'completed',
            'report_path': str(preview_path)
        }
        
    except Exception as e:
        logger.error(f"Preview generation failed: {e}")
        report['steps']['preview'] = {
            'status': 'failed',
            'error': str(e)
        }
    
    # STEP 5: Final Cleaning (skip if preview_only)
    if preview_only:
        logger.info("PREVIEW MODE: Skipping final cleaning")
        report['mode'] = 'preview_only'
        report['steps']['final_cleaning'] = {'status': 'skipped', 'reason': 'preview_only mode'}
    else:
        logger.info("STEP 5: Final Cleaning")
        
        # Remove headers/footers
        temp_cleaned = str(output_dir / f"{base_name}_temp_cleaned.pdf")
        try:
            hf_detector.remove_headers_footers(
                versions['ocr'],
                temp_cleaned,
                hf_results['headers'],
                hf_results['footers']
            )
        except Exception as e:
            logger.error(f"Header/footer removal failed: {e}")
            # Use OCR version if this fails
            import shutil
            shutil.copy(versions['ocr'], temp_cleaned)
        
        # Remove decorative images
        try:
            removed_count = img_classifier.remove_decorative_images(
                temp_cleaned,
                versions['cleaned'],
                img_results['decorative_images']
            )
            report['steps']['final_cleaning'] = {
                'status': 'completed',
                'headers_footers_removed': len(hf_results['headers']) + len(hf_results['footers']),
                'images_removed': removed_count
            }
        except Exception as e:
            logger.error(f"Image removal failed: {e}")
            import shutil
            shutil.copy(temp_cleaned, versions['cleaned'])
            report['steps']['final_cleaning'] = {
                'status': 'partial',
                'error': str(e)
            }
        
        # Cleanup temp file
        try:
            Path(temp_cleaned).unlink()
        except:
            pass
    
    # STEP 6: Text Extraction
    logger.info("STEP 6: Text Extraction")
    try:
        # Extract from cleaned version (or OCR if preview_only)
        source_pdf = versions['cleaned'] if not preview_only else versions['ocr']
        
        if not Path(source_pdf).exists():
            source_pdf = versions['ocr']
        
        text_result = text_extractor.extract_text(
            source_pdf,
            hf_results.get('headers', []),
            hf_results.get('footers', [])
        )
        
        # Save text file
        text_output_path = output_dir / f"{base_name}_cleaned.txt"
        text_extractor.save_text(text_result['text'], str(text_output_path))
        
        # Generate chunk simulation
        if config.get('output', {}).get('generate_chunk_simulation', True):
            chunk_size = config.get('output', {}).get('simulation_chunk_size', 2000)
            chunks = text_extractor.generate_chunk_simulation(text_result['text'], chunk_size)
            
            # Save chunk simulation
            chunk_path = output_dir / f"{base_name}_chunk_simulation.txt"
            with open(chunk_path, 'w', encoding='utf-8') as f:
                for i, chunk in enumerate(chunks):
                    f.write(f"=== CHUNK {i+1}/{len(chunks)} ===\n")
                    f.write(chunk)
                    f.write("\n\n")
            
            report['steps']['text_extraction'] = {
                'status': 'completed',
                'text_file': str(text_output_path),
                'chunk_simulation': str(chunk_path),
                'total_characters': len(text_result['text']),
                'total_chunks': len(chunks),
                'rtl_pages': len(text_result['rtl_pages']),
                'ltr_pages': len(text_result['ltr_pages'])
            }
        
        logger.info(f"Text extracted: {len(text_result['text'])} characters")
        
    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
        report['steps']['text_extraction'] = {
            'status': 'failed',
            'error': str(e)
        }
    
    # Finalize report
    end_time = time.time()
    report['end_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
    report['duration_seconds'] = round(end_time - start_time, 2)
    report['status'] = 'completed'
    
    return report


def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(
        description='PDF Cleaning Tool for Gemini File Search Preparation'
    )
    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    parser.add_argument(
        '--preview',
        action='store_true',
        help='Preview mode: show analysis without final processing'
    )
    parser.add_argument(
        '--file',
        help='Process a single PDF file (otherwise process all PDFs in input_dir)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.verbose)
    
    logger.info("="*60)
    logger.info("PDF Cleaning Tool")
    logger.info("="*60)
    
    # Load configuration
    try:
        config = load_config(args.config)
        logger.info(f"Loaded configuration from {args.config}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return 1
    
    # Check if preview mode is forced in config
    if config.get('preview', {}).get('preview_only', False):
        logger.info("Preview mode enabled in config")
        args.preview = True
    
    if args.preview:
        logger.warning("PREVIEW MODE: No files will be modified")
    
    # Determine which files to process
    if args.file:
        pdf_files = [args.file]
    else:
        input_dir = Path(config.get('input_dir', 'context'))
        pdf_files = list(input_dir.glob('*.pdf'))
    
    if not pdf_files:
        logger.error("No PDF files found to process")
        return 1
    
    logger.info(f"Found {len(pdf_files)} PDF file(s) to process")
    
    # Process each file
    all_reports = []
    
    for pdf_file in pdf_files:
        logger.info("")
        logger.info("="*60)
        logger.info(f"Processing: {pdf_file}")
        logger.info("="*60)
        
        try:
            report = process_pdf_file(str(pdf_file), config, args.preview)
            all_reports.append(report)
        except Exception as e:
            logger.error(f"Failed to process {pdf_file}: {e}")
            import traceback
            traceback.print_exc()
    
    # Save combined report
    report_dir = Path(config.get('report_dir', 'report'))
    report_dir.mkdir(parents=True, exist_ok=True)
    
    combined_report = {
        'total_files': len(pdf_files),
        'processed': len(all_reports),
        'preview_mode': args.preview,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'files': all_reports
    }
    
    report_path = report_dir / 'cleaning_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(combined_report, f, ensure_ascii=False, indent=2)
    
    logger.info("")
    logger.info("="*60)
    logger.info(f"Processing complete! Processed {len(all_reports)}/{len(pdf_files)} files")
    logger.info(f"Full report saved to: {report_path}")
    logger.info("="*60)
    
    if args.preview:
        logger.info("")
        logger.info("NEXT STEPS:")
        logger.info("1. Review the preview reports in the 'report/' directory")
        logger.info("2. Check sample pages and detection results")
        logger.info("3. If satisfied, run again without --preview flag:")
        logger.info(f"   python3 scripts/clean_pdfs.py")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
