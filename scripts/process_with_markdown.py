#!/usr/bin/env python3
"""
Process PDF with Enhanced Markdown Structuring
معالجة PDF مع هيكلة Markdown محسّنة

This script uses the enhanced text processor to:
1. Extract text with Markdown headers (# ##) based on font size
2. Remove Quranic noise (broken font artifacts) while preserving valid English terms
3. Apply proper RTL formatting with arabic-reshaper
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.enhanced_text_processor import EnhancedTextProcessor
import yaml


def setup_logging():
    """Setup basic logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def load_config():
    """Load configuration"""
    config_path = 'config.yaml'
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"Error loading config: {e}")
        print("Using default config...")
        return {
            'text': {
                'enable_markdown': True,
                'h1_font_size': 16,
                'h2_font_size': 14,
                'remove_quranic_noise': True,
                'quranic_placeholder': '[نص قرآني]'
            }
        }


def main():
    """Main processing function"""
    
    logger = setup_logging()
    
    print("=" * 70)
    print("📄 Enhanced PDF Processing with Markdown Structuring")
    print("=" * 70)
    print()
    
    # Check arguments
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/process_with_markdown.py <pdf_file>")
        print()
        print("Example:")
        print("  python3 scripts/process_with_markdown.py context/AAOIFI_AR.pdf")
        print()
        print("This will create:")
        print("  - filename_structured.md  (Markdown with headers)")
        print("  - filename_clean.txt       (Plain text, cleaned)")
        print("  - filename_rtl.txt         (RTL formatted text)")
        return 1
    
    pdf_path = Path(sys.argv[1])
    
    if not pdf_path.exists():
        print(f"❌ File not found: {pdf_path}")
        return 1
    
    print(f"📖 Processing: {pdf_path.name}")
    print()
    
    # Load config
    config = load_config()
    
    # Initialize enhanced processor
    processor = EnhancedTextProcessor(config)
    
    # Extract structured text
    print("🔍 Extracting text with Markdown structure...")
    result = processor.extract_text_with_structure(str(pdf_path))
    
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
    
    # Save Markdown file
    markdown_path = output_dir / f"{base_name}_structured.md"
    processor.save_markdown_file(result['markdown_text'], str(markdown_path))
    print(f"💾 Saved Markdown: {markdown_path}")
    
    # Save plain text (cleaned)
    plain_path = output_dir / f"{base_name}_clean.txt"
    with open(plain_path, 'w', encoding='utf-8') as f:
        f.write(result['plain_text'])
    print(f"💾 Saved plain text: {plain_path}")
    
    # Save RTL formatted text
    rtl_path = output_dir / f"{base_name}_rtl.txt"
    processor.save_rtl_text_file(result['plain_text'], str(rtl_path))
    print(f"💾 Saved RTL text: {rtl_path}")
    
    print()
    print("=" * 70)
    print("✅ Processing Complete!")
    print("=" * 70)
    print()
    print("📝 Next steps:")
    print(f"1. Review the Markdown file: {markdown_path}")
    print(f"   - Check that headers are properly formatted with # and ##")
    print(f"   - Verify Quranic verses are replaced with {config['text'].get('quranic_placeholder', '[نص قرآني]')}")
    print(f"   - Confirm English terms like SUKUK, MURABAHA are preserved")
    print()
    print(f"2. Upload {markdown_path} to Gemini File Search")
    print(f"   - The Markdown structure helps Gemini understand document hierarchy")
    print(f"   - Clean text improves RAG accuracy significantly")
    print()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
