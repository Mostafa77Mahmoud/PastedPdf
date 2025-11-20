#!/usr/bin/env python3
"""
Large PDF Processing Script - معالج الملفات الضخمة
Uses memory-optimized batched processing for PDFs with 500+ pages
"""

import sys
import logging
from pathlib import Path
import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import pdfplumber
except ImportError:
    print("Error: pdfplumber not installed")
    sys.exit(1)

from services.enhanced_text_processor import EnhancedTextProcessor


def setup_logging():
    """Setup basic logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def load_config():
    """Load configuration from config.yaml"""
    config_path = Path('config.yaml')
    
    if not config_path.exists():
        print("⚠️  config.yaml not found, using defaults")
        return {
            'text': {
                'enable_markdown': True,
                'h1_font_size': 20,
                'h2_font_size': 15,
                'remove_quranic_noise': True,
                'quranic_placeholder': '[نص قرآني]'
            }
        }
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"Error loading config: {e}")
        return None


def main():
    """Main processing function"""
    
    logger = setup_logging()
    
    print("=" * 70)
    print("📄 Large PDF Processing (Memory-Optimized)")
    print("=" * 70)
    print()
    
    # Check arguments
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/process_large_pdf.py <pdf_file> [batch_size]")
        print()
        print("Example:")
        print("  python3 scripts/process_large_pdf.py context/large_file.pdf")
        print("  python3 scripts/process_large_pdf.py context/large_file.pdf 50")
        print()
        print("This will create:")
        print("  - filename_structured.md  (Markdown with headers)")
        print("  - filename_clean.txt       (Plain text, cleaned)")
        return 1
    
    pdf_path = Path(sys.argv[1])
    
    if not pdf_path.exists():
        print(f"❌ File not found: {pdf_path}")
        return 1
    
    # Get batch size from argument or use default
    batch_size = 50
    if len(sys.argv) >= 3:
        try:
            batch_size = int(sys.argv[2])
        except ValueError:
            print(f"⚠️  Invalid batch_size, using default: 50")
    
    print(f"📖 Processing: {pdf_path.name}")
    print(f"📦 Batch size: {batch_size} pages")
    print()
    
    # Load config
    config = load_config()
    if not config:
        return 1
    
    # Initialize processor
    processor = EnhancedTextProcessor(config)
    
    # Process PDF in batches
    print("🔍 Processing PDF in batches (this may take several minutes)...")
    print()
    
    try:
        result = processor.extract_text_with_structure_batched(str(pdf_path), batch_size)
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        return 1
    
    print()
    print("=" * 70)
    print("📊 Processing Results")
    print("=" * 70)
    
    # Display structure info
    structure = result['structure_info']
    print(f"✅ Structure detected:")
    print(f"   - H1 headers (# ):  {structure['h1_count']}")
    print(f"   - H2 headers (##):  {structure['h2_count']}")
    print(f"   - Body paragraphs:  {structure['body_count']}")
    print()
    
    # Display cleaning stats
    stats = result['cleaning_stats']
    print(f"✅ Text cleaning:")
    print(f"   - Quranic sequences removed:    {stats['quranic_sequences_removed']}")
    print(f"   - English terms preserved:      {stats['english_terms_preserved']}")
    print()
    
    # Save files
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    
    base_name = pdf_path.stem
    
    # Save Markdown file (Logical Order - for Gemini)
    markdown_path = output_dir / f"{base_name}_structured.md"
    processor.save_markdown_file(result['markdown_text'], str(markdown_path))
    print(f"💾 Saved Markdown: {markdown_path}")
    
    # Save plain text (Logical Order)
    plain_path = output_dir / f"{base_name}_clean.txt"
    with open(plain_path, 'w', encoding='utf-8') as f:
        f.write(result['plain_text'])
    print(f"💾 Saved plain text: {plain_path}")
    
    print()
    print("=" * 70)
    print("✅ Processing Complete!")
    print("=" * 70)
    print()
    print("📤 Next Steps:")
    print(f"   1. Review the output: {markdown_path}")
    print("   2. Upload _structured.md to Gemini File Search")
    print("   3. Test with queries like:")
    print('      "ما هو تعريف المرابحة؟"')
    print('      "ما هي شروط الإجارة؟"')
    print()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
